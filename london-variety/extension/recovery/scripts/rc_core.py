"""2SLS with one endogenous regressor and one instrument, for the recovery extension.

Fixed effects nested in the clusters (LA effects with LA clusters) are removed by within-demeaning, which commutes
with cluster-constant bootstrap weights; other exogenous regressors (controls, region dummies) stay in W and are
partialled out by projection. Standard errors are CR1 with fixest-style degrees of freedom, as in es_core:
c = G/(G-1) * (n-1)/(n-k), k = columns of W + 1 (+1 when nested effects were absorbed). Confidence intervals use
t(G-1). The Anderson-Rubin test of beta = b0 regresses y - b0*d on z and W and tests z, with CR1 p-values and wild
cluster restricted bootstrap p-values from es_core.fit_cluster (Rademacher, B = 9,999, seed 20261028).
"""
import numpy as np
import pandas as pd
from scipy import stats

import rc_common  # noqa: F401  (paths)
from e_core import B, SEED  # noqa: E402
from es_core import fit_cluster, rademacher  # noqa: E402

GRID = np.round(np.arange(-5, 5.0001, 0.005), 3)


def prep(df, y, d, z, controls, fe=None, cluster="lad23cd", region_fe=None):
    cols = [y, d, z] + list(controls) + [cluster] + ([fe] if fe else []) + ([region_fe] if region_fe else [])
    x = df.dropna(subset=cols).copy()
    if fe:
        x = x[x.groupby(fe)[fe].transform("size") > 1]
    names = [y, d, z] + list(controls)
    A = x[names].astype(float)
    if fe:
        A = A - A.groupby(x[fe].values).transform("mean")
        W = A[list(controls)].values
        k_extra = 1
    else:
        parts = [A[list(controls)].values]
        if region_fe:
            parts.append(pd.get_dummies(x[region_fe], dtype=float).values)
        else:
            parts.append(np.ones((len(x), 1)))
        W = np.hstack(parts)
        k_extra = 0
    return dict(y=A[y].values, d=A[d].values, z=A[z].values, W=W, cl=x[cluster].values, n=len(x),
                k=W.shape[1] + 1 + k_extra, frame=x)


def _resid(v, W):
    if W.shape[1] == 0:
        return v
    return v - W @ np.linalg.lstsq(W, v, rcond=None)[0]


def _clsum(cl, v):
    g, inv = np.unique(cl, return_inverse=True)
    return np.bincount(inv, weights=v, minlength=len(g)), len(g)


def iv(P, ols=False, boot=True):
    """Returns a dict: beta, se, CI, Wald p against -1 and 0, AR tests and set, first stage."""
    W, cl, n, k = P["W"], P["cl"], P["n"], P["k"]
    yt, dt, zt = _resid(P["y"], W), _resid(P["d"], W), _resid(P["z"], W)
    if ols:
        zt = dt
    G = len(np.unique(cl))
    c = G / (G - 1) * (n - 1) / (n - k)
    crit = stats.t.ppf(0.975, G - 1)
    zd = zt @ dt
    beta = (zt @ yt) / zd
    u = yt - beta * dt
    s, _ = _clsum(cl, zt * u)
    se = np.sqrt(c * (s ** 2).sum()) / abs(zd)
    pt = lambda t: 2 * stats.t.sf(abs(t), G - 1)
    out = dict(beta=beta, se=se, ci_lo=beta - crit * se, ci_hi=beta + crit * se,
               p_wald_m1=pt((beta + 1) / se), p_wald_0=pt(beta / se), n=n, G=G)
    if ols:
        return out
    # first stage
    zz = zt @ zt
    pi = (zt @ dt) / zz
    v = dt - pi * zt
    sv, _ = _clsum(cl, zt * v)
    fse = np.sqrt(c * (sv ** 2).sum()) / zz
    out.update(fs_coef=pi, fs_se=fse, fs_F=(pi / fse) ** 2)
    # Anderson-Rubin: grid with CR1
    Sy, _ = _clsum(cl, zt * yt)
    Sd, _ = _clsum(cl, zt * dt)
    Sz, _ = _clsum(cl, zt * zt)
    ay, ad = (zt @ yt) / zz, (zt @ dt) / zz
    a = ay - GRID * ad
    sg = Sy[None, :] - GRID[:, None] * Sd[None, :] - a[:, None] * Sz[None, :]
    ase = np.sqrt(c * (sg ** 2).sum(axis=1)) / zz
    ap = pt(a / ase)
    acc = GRID[ap >= 0.05]
    if len(acc) == 0:
        aset = "empty"
    else:
        gaps = np.where(np.diff(acc) > 0.0051)[0]
        pieces, start = [], 0
        for gi in list(gaps) + [len(acc) - 1]:
            pieces.append((acc[start], acc[gi]))
            start = gi + 1
        txt = []
        for lo, hi in pieces:
            lo_s = "-inf" if lo <= GRID[0] else f"{lo:.2f}"
            hi_s = "+inf" if hi >= GRID[-1] else f"{hi:.2f}"
            txt.append(f"[{lo_s}, {hi_s}]")
        aset = " U ".join(txt)
    out.update(ar_set=aset, ar_lo=acc.min() if len(acc) else np.nan, ar_hi=acc.max() if len(acc) else np.nan,
               ar_unbounded=bool(len(acc) and (acc.min() <= GRID[0] or acc.max() >= GRID[-1])))
    for b0, lab in [(-1.0, "m1"), (0.0, "0")]:
        i = int(np.argmin(np.abs(GRID - b0)))
        out[f"ar_p_{lab}_cr1"] = ap[i]
        if boot:
            Xb = np.column_stack([P["z"], W]) if W.shape[1] else P["z"][:, None]
            nm = ["z"] + [f"w{j}" for j in range(W.shape[1])]
            w = rademacher(B, G, SEED)
            tab, _ = fit_cluster(Xb, P["y"] - b0 * P["d"], nm, ["z"], cl_se=cl, w=w,
                                 k_absorbed_counted=1 if k > W.shape[1] + 1 else 0)
            out[f"ar_p_{lab}_wcb"] = float(tab.p_wcb.iloc[0])
        else:
            out[f"ar_p_{lab}_wcb"] = np.nan
    out["influence"] = (cl, zt * u / zd)
    return out


def classify(r):
    """Registered rule: Wald 95% CI if first-stage F >= 10, else the Anderson-Rubin set."""
    if "fs_F" in r and r["fs_F"] < 10:
        used = "AR"
        if r["ar_set"] == "empty":
            return used, "inconclusive (empty AR set)"
        if r["ar_unbounded"] or " U " in r["ar_set"]:
            lo, hi = r["ar_lo"], r["ar_hi"]
            if r["ar_unbounded"]:
                return used, "inconclusive (unbounded AR set)"
        lo, hi = r["ar_lo"], r["ar_hi"]
        has = lambda b: (r["ar_p_m1_cr1"] >= 0.05) if b == -1 else (r["ar_p_0_cr1"] >= 0.05)
    else:
        used = "Wald" if "fs_F" in r else "Wald (OLS)"
        lo, hi = r["ci_lo"], r["ci_hi"]
        has = lambda b: lo <= b <= hi
    c1, c0 = has(-1), has(0)
    if c1 and not c0:
        return used, "full recovery"
    if c0 and not c1:
        return used, "lasting shift"
    if c1 and c0:
        return used, "inconclusive"
    b = r["beta"]
    if -1 < b < 0:
        return used, "partial recovery"
    return used, "over-recovery (below -1)" if b <= -1 else "shock deepened (above 0)"


def run(df, y, d, z, controls, label, ols=False, boot=True, **kw):
    P = prep(df, y, d, z, controls, **kw)
    r = iv(P, ols=ols, boot=boot)
    used, cls = classify(r)
    r.update(label=label, method="OLS" if ols else "2SLS", outcome=y, endog=d, instrument="-" if ols else z,
             interval_used=used, classification=cls)
    return r


COLS = ["label", "method", "instrument", "beta", "se", "ci_lo", "ci_hi", "p_wald_m1", "p_wald_0", "fs_coef", "fs_se",
        "fs_F", "ar_set", "ar_p_m1_cr1", "ar_p_m1_wcb", "ar_p_0_cr1", "ar_p_0_wcb", "interval_used",
        "classification", "n", "G"]


def table(rows):
    return pd.DataFrame([{c: r.get(c, np.nan) for c in COLS} for r in rows])


def md(t, title):
    L = [f"# {title}", "",
         "| Model | Method | beta | 95% CI | p vs -1 | p vs 0 | First stage (SE) | F | AR 95% set | AR p vs -1 (WCB) | AR p vs 0 (WCB) | Reading | n | G |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda v, d=2: "" if pd.isna(v) else f"{v:.{d}f}"
    for _, r in t.iterrows():
        fs = "" if pd.isna(r.fs_coef) else f"{r.fs_coef:.4f} ({r.fs_se:.4f})"
        L.append(f"| {r.label} | {r.method} | {f(r.beta)} | [{f(r.ci_lo)}, {f(r.ci_hi)}] | {f(r.p_wald_m1, 3)} | "
                 f"{f(r.p_wald_0, 3)} | {fs} | {f(r.fs_F, 1)} | {'' if pd.isna(r.ar_set) else r.ar_set} | "
                 f"{f(r.ar_p_m1_wcb, 3)} | {f(r.ar_p_0_wcb, 3)} | {r.classification} ({r.interval_used}) | {int(r.n)} | {int(r.G)} |")
    return "\n".join(L) + "\n"
