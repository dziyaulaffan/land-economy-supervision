# HonestDiD sensitivity (Rambachan and Roth 2023) for the baseline continuous event studies.
#
# Inputs (written by 80_event_study.py): regression_table.csv (coefficients) and
# vcov_<outcome>_continuous_baseline.csv (CR1 borough-clustered covariance of the event-time
# coefficients). The omitted period (2019 / 2019Q4) is the last pre-period, as HonestDiD expects.
#
# Restrictions: relative magnitudes (Delta^RM, Mbar) and smoothness (Delta^SD, M).
# Breakdown value = smallest Mbar (or M) at which the robust 95% CI includes zero.
# Relative magnitudes are slow (about 4 minutes per Mbar value for rents with 19 pre-periods at
# HonestDiD's default 1,000 grid points), so: a coarse Mbar grid run in parallel for the plots, then
# bisection between the bracketing grid values for the breakdown (precision 0.25/2^4 = 0.016), with
# gridPoints = 250 for the test inversion.
# Usage: Rscript 83_honestdid.R <event_study_dir>

args <- commandArgs(trailingOnly = TRUE)
es_dir <- args[1]
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))
suppressPackageStartupMessages({
  library(HonestDiD)
  library(ggplot2)
  library(doParallel)
})
registerDoParallel(cores = max(1, min(8, parallel::detectCores() - 2)))

GRID_POINTS <- 250
MBAR_GRID <- c(0, 0.25, 0.5, 0.75, 1, 1.5, 2)
BISECT_STEPS <- 4

tab <- read.csv(file.path(es_dir, "regression_table.csv"), colClasses = c(period = "character"))
targets <- list(
  migration = list(base = "2019",
                   t = list(first_post = "2020", avg_2020_2021 = c("2020", "2021"))),
  rents = list(base = "2019Q4",
               t = list(q4_2021 = "2021Q4",
                        avg_2020Q1_2022Q4 = sprintf("%d%s", rep(2020:2022, each = 4), paste0("Q", 1:4))))
)

includes0 <- function(r) r$lb <= 0 & r$ub >= 0

summary_rows <- list()
for (outcome in names(targets)) {
  o <- targets[[outcome]]
  d <- tab[tab$outcome == outcome & tab$treatment == "continuous" & tab$spec == "baseline", ]
  d <- d[order(d$period), ]
  V <- as.matrix(read.csv(file.path(es_dir, sprintf("vcov_%s_continuous_baseline.csv", outcome)), row.names = 1,
                          check.names = FALSE))
  key <- paste0("D_cont:", d$period)
  V <- V[key, key]
  V <- (V + t(V)) / 2
  betahat <- d$coef
  pre <- d$period < o$base
  n_pre <- sum(pre); n_post <- sum(!pre)
  post_periods <- d$period[!pre]
  # smoothness grid: up to 3x the largest absolute second difference of the pre-period path
  # (pre coefficients plus the normalised zero at the base period)
  path <- c(betahat[pre], 0)
  m_max <- 3 * max(abs(diff(path, differences = 2)))
  m_grid <- seq(0, m_max, length.out = 41)
  cat(sprintf("%s: %d pre, %d post periods; smoothness grid 0..%.3f\n", outcome, n_pre, n_post, m_max))

  for (tn in names(o$t)) {
    sel <- post_periods %in% o$t[[tn]]
    l_vec <- matrix(as.numeric(sel) / sum(sel), ncol = 1)
    orig <- constructOriginalCS(betahat = betahat, sigma = V, numPrePeriods = n_pre,
                                numPostPeriods = n_post, l_vec = l_vec)
    rm_at <- function(mb) createSensitivityResults_relativeMagnitudes(
      betahat = betahat, sigma = V, numPrePeriods = n_pre, numPostPeriods = n_post, l_vec = l_vec,
      Mbarvec = mb, alpha = 0.05, gridPoints = GRID_POINTS, parallel = length(mb) > 1)
    t0 <- Sys.time()
    rm <- rm_at(MBAR_GRID)
    rm <- rm[order(rm$Mbar), ]
    # breakdown by bisection between the last grid value excluding 0 and the first including it
    inc <- includes0(rm)
    if (inc[1]) {
      bd_rm <- 0; bd_note <- "CI includes 0 at Mbar = 0"
    } else if (!any(inc)) {
      bd_rm <- NA; bd_note <- sprintf("CI excludes 0 for all Mbar <= %.2f", max(MBAR_GRID))
    } else {
      hi <- rm$Mbar[which(inc)[1]]; lo <- max(rm$Mbar[rm$Mbar < hi & !inc])
      for (i in seq_len(BISECT_STEPS)) {
        mid <- (lo + hi) / 2
        r <- rm_at(mid); rm <- rbind(rm, r)
        if (includes0(r)) hi <- mid else lo <- mid
      }
      bd_rm <- hi; bd_note <- sprintf("bracketed in (%.3f, %.3f]", lo, hi)
      rm <- rm[order(rm$Mbar), ]
    }
    sd <- createSensitivityResults(betahat = betahat, sigma = V, numPrePeriods = n_pre,
                                   numPostPeriods = n_post, l_vec = l_vec, Mvec = m_grid, alpha = 0.05)
    inc_sd <- includes0(sd)
    bd_sd <- if (any(inc_sd)) min(sd$M[inc_sd]) else NA
    cat(sprintf("  %s done in %.0fs; RM breakdown %s (%s); SD breakdown %s\n", tn,
                as.numeric(difftime(Sys.time(), t0, units = "secs")), format(bd_rm), bd_note, format(bd_sd)))

    rm$outcome <- outcome; rm$target <- tn
    sd$outcome <- outcome; sd$target <- tn
    write.csv(as.data.frame(rm), file.path(es_dir, sprintf("honestdid_%s_%s_rm.csv", outcome, tn)), row.names = FALSE)
    write.csv(as.data.frame(sd), file.path(es_dir, sprintf("honestdid_%s_%s_sd.csv", outcome, tn)), row.names = FALSE)

    summary_rows[[length(summary_rows) + 1]] <- data.frame(
      outcome = outcome, target = tn, periods = paste(o$t[[tn]], collapse = "+"),
      estimate = sum(l_vec * betahat[!pre]), orig_lb = orig$lb, orig_ub = orig$ub,
      breakdown_Mbar_RM = bd_rm, RM_note = bd_note,
      breakdown_M_SD = bd_sd, SD_grid_step = m_grid[2], SD_grid_max = m_max,
      SD_M0_lb = sd$lb[1], SD_M0_ub = sd$ub[1])

    p1 <- createSensitivityPlot_relativeMagnitudes(rm[rm$Mbar %in% MBAR_GRID, ], orig) +
      labs(title = sprintf("%s, %s: relative magnitudes", outcome, tn),
           subtitle = sprintf("Robust 95%% CI by Mbar; breakdown Mbar = %s", format(round(bd_rm, 3))))
    p2 <- createSensitivityPlot(sd, orig) +
      labs(title = sprintf("%s, %s: smoothness", outcome, tn),
           subtitle = sprintf("Robust 95%% CI by M (M = 0: linear extrapolation of pre-trend); breakdown M = %s",
                              format(round(bd_sd, 3))))
    ggsave(file.path(es_dir, sprintf("honestdid_%s_%s_rm.png", outcome, tn)), p1, width = 7, height = 4.5, dpi = 150)
    ggsave(file.path(es_dir, sprintf("honestdid_%s_%s_sd.png", outcome, tn)), p2, width = 7, height = 4.5, dpi = 150)
  }
}
s <- do.call(rbind, summary_rows)
write.csv(s, file.path(es_dir, "honestdid_breakdown.csv"), row.names = FALSE)
print(s)
