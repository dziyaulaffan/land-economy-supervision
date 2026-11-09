# Robustness: Callaway, Goodman-Bacon and Sant'Anna continuous DiD on quarterly rents.
#
# Package: contdid (CRAN), cont_did(). The estimator needs an untreated comparison group
# (gname = 0). Every London borough has positive amenity density and the pandemic hit all of
# them in the same quarter, so there is no untreated group in the data. Judgement call: the
# bottom within-zone amenity tercile (10 boroughs, the binned reference group) is treated as the
# comparison group, and the other 22 boroughs are "treated" from 2020Q1 with dose =
# log(I+R local units per 1,000). Results are therefore effects relative to low-amenity boroughs,
# not relative to zero amenity.
#
# Usage: Rscript 85_contdid.R <clean_dir> <out_dir>

args <- commandArgs(trailingOnly = TRUE)
clean_dir <- args[1]
out_dir <- args[2]
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))
suppressPackageStartupMessages({
  library(contdid)
  library(ggplot2)
})
set.seed(20261028)

d <- read.csv(file.path(clean_dir, "event_study_rents_quarterly.csv"))
quarters <- sort(unique(d$period))
d$t <- match(d$period, quarters)
d$id <- as.integer(factor(d$la_code))
treat_q <- match("2020Q1", quarters)
d$g <- ifelse(d$tercile > 1, treat_q, 0)
d$dose <- ifelse(d$tercile > 1, log(d$per1k_IR), 0)
d$dose_bin <- as.numeric(d$tercile > 1)  # level/eventstudy binarises the treatment and needs a 0/1 dose
cat(sprintf("units: %d treated, %d comparison; periods: %d (2020Q1 = t%d)\n",
            length(unique(d$id[d$g > 0])), length(unique(d$id[d$g == 0])), length(quarters), treat_q))

runs <- list(
  es_level = list(target = "level", agg = "eventstudy", dname = "dose_bin"),
  es_slope = list(target = "slope", agg = "eventstudy"),
  dose_level = list(target = "level", agg = "dose"),
  dose_slope = list(target = "slope", agg = "dose")
)
log_lines <- c()
for (nm in names(runs)) {
  r <- runs[[nm]]
  dn <- if (is.null(r$dname)) "dose" else r$dname
  warns <- character(0)
  res <- tryCatch(withCallingHandlers(
    cont_did(yname = "y", dname = dn, gname = "g", tname = "t", idname = "id", data = d,
             target_parameter = r$target, aggregation = r$agg, treatment_type = "continuous",
             dose_est_method = "parametric", degree = 1, num_knots = 0,
             control_group = "nevertreated", base_period = "universal",
             biters = 999, cband = FALSE),  # clusters by idname by default
    warning = function(w) { warns <<- c(warns, conditionMessage(w)); invokeRestart("muffleWarning") }),
    error = function(e) e)
  if (length(warns)) log_lines <- c(log_lines, sprintf("%s: %d warnings, distinct: %s", nm, length(warns),
                                                      paste(unique(warns), collapse = " | ")))
  if (inherits(res, "error")) {
    msg <- sprintf("%s: FAILED - %s", nm, conditionMessage(res))
    cat(msg, "\n"); log_lines <- c(log_lines, msg); next
  }
  out <- capture.output(print(summary(res)))
  writeLines(out, file.path(out_dir, sprintf("contdid_rents_%s.txt", nm)))
  p <- tryCatch(ggcont_did(res), error = function(e) NULL)
  if (!is.null(p)) {
    if (r$agg == "eventstudy") p <- p + labs(x = sprintf("Quarters since 2020Q1 (event time 0 = t%d)", treat_q))
    p <- p + labs(title = sprintf("contdid, rents: %s / %s", r$target, r$agg),
                  subtitle = "Comparison group: bottom within-zone amenity tercile (10 boroughs)")
    ggsave(file.path(out_dir, sprintf("contdid_rents_%s.png", nm)), p, width = 7, height = 4.5, dpi = 150)
  }
  log_lines <- c(log_lines, sprintf("%s: ok", nm))
  cat(nm, "ok\n")
}
writeLines(log_lines, file.path(out_dir, "contdid_rents_log.txt"))
