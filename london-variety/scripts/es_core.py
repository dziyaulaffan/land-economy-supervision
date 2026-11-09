"""Shared OLS + cluster-robust + wild cluster restricted bootstrap (WCR) machinery.

Works on a design matrix X that already contains (or has been partialled of) all fixed effects.
Cluster sums use sparse indicator matrices, so it scales to several hundred thousand rows.

WCR for coefficient j (null beta_j = 0 imposed), Rademacher weights constant within bootstrap
cluster g. With x~ = M_{-j} x_j and restricted residuals u_r = u + beta_j x~:
    beta*_j        = a'w / x~'x~,                 a_g = sum_{i in g} x~_i u_r,i
    cluster scores = C w,  C = diag(a) - (S_x X)(X'X)^{-1}(S_u X)'
where S_x, S_u are G x n sparse matrices holding x~ and u_r at (g_i, i). The bootstrap t uses the
same CR1 factor as the original t, so p-values do not depend on it.
FWL note: fixed effects may be partialled out of y and X beforehand only if every partialled
fixed effect is nested within the bootstrap clusters; otherwise M_FE(u_r * w) != u_r * w.
"""
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy import stats


def rademacher(B: int, G: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).choice([-1.0, 1.0], size=(B, G))


def _indicator(codes: np.ndarray, values: np.ndarray, G: int) -> sp.csr_matrix:
    n = len(codes)
    return sp.csr_matrix((values, (codes, np.arange(n))), shape=(G, n))


def fit_cluster(X, y, names, tested, cl_se, cl_boot=None, w=None, k_absorbed_counted=0, k_nested=0,
                contrasts=None):
    """OLS with CR1 SEs clustered on cl_se and WCR bootstrap p-values clustered on cl_boot.

    k_nested: columns of X that are fixed effects nested in cl_se (not counted in K, fixest style).
    k_absorbed_counted: fixed effects partialled out beforehand that ARE counted in K.
    contrasts: optional {label: {column name: weight}}; each linear combination c'beta is reported and
        tested (null c'beta = 0) exactly like a single coefficient. With a = X(X'X)^{-1}c and
        s = c'(X'X)^{-1}c, x~ = a / s plays the role of M_{-j} x_j (c = e_j recovers the single case).
    Returns (table of tested coefficients then contrasts, covariance matrix of tested coefficients).
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    n, k = X.shape
    XtX = X.T @ X
    L = np.linalg.cholesky(XtX)
    XtXinv = np.linalg.inv(L).T @ np.linalg.inv(L)
    beta = XtXinv @ (X.T @ y)
    u = y - X @ beta

    g_se, inv_se = np.unique(cl_se, return_inverse=True)
    G = len(g_se)
    k_eff = k - k_nested + 1 + k_absorbed_counted
    c = G / (G - 1) * (n - 1) / (n - k_eff)
    S = (_indicator(inv_se, u, G) @ X)            # G x k cluster scores
    idx = [names.index(t) for t in tested]
    A = XtXinv[:, idx]
    V = c * A.T @ (S.T @ S) @ A                    # covariance of tested coefficients
    se = np.sqrt(np.diag(V))
    tval = beta[idx] / se
    crit = stats.t.ppf(0.975, G - 1)
    # every reported quantity as a contrast vector: unit vectors for tested coefficients, then contrasts
    cvecs = []
    for j in idx:
        e = np.zeros(k); e[j] = 1.0
        cvecs.append(e)
    labels = list(tested)
    for lab, wts in (contrasts or {}).items():
        cv = np.zeros(k)
        for nm, wt in wts.items():
            cv[names.index(nm)] = wt
        cvecs.append(cv)
        labels.append(lab)
    Cm = np.column_stack(cvecs)
    est = Cm.T @ beta
    se_all = np.sqrt(np.diag(c * (XtXinv @ Cm).T @ (S.T @ S) @ (XtXinv @ Cm)))
    t_all = est / se_all
    out = pd.DataFrame({"name": labels, "coef": est, "se_cluster": se_all, "t": t_all,
                        "p_cluster": 2 * stats.t.sf(np.abs(t_all), G - 1),
                        "ci_low": est - crit * se_all, "ci_high": est + crit * se_all})

    if w is not None:
        cl_boot = cl_se if cl_boot is None else cl_boot
        g_b, inv_b = np.unique(cl_boot, return_inverse=True)
        Gb = len(g_b)
        assert w.shape[1] == Gb, "bootstrap weights do not match number of bootstrap clusters"
        cb = Gb / (Gb - 1) * (n - 1) / (n - k_eff)
        ones = np.ones(n)
        pw, t_b = [], []
        for cv, b0 in zip(cvecs, est):
            av = XtXinv @ cv
            xt = X @ (av / (cv @ av))
            sxx = xt @ xt
            # analytic t with bootstrap clusters (the statistic being bootstrapped)
            sc = _indicator(inv_b, xt * u, Gb) @ ones
            t0 = b0 / (np.sqrt(cb * (sc ** 2).sum()) / sxx)
            ur = u + b0 * xt
            a = _indicator(inv_b, xt * ur, Gb) @ ones
            Sx = _indicator(inv_b, xt, Gb) @ X          # Gb x k
            Su = _indicator(inv_b, ur, Gb) @ X          # Gb x k
            C = np.diag(a) - Sx @ XtXinv @ Su.T
            tstar = (w @ a) / np.sqrt(cb * ((w @ C.T) ** 2).sum(axis=1))
            pw.append((np.abs(tstar) >= abs(t0)).mean())
            t_b.append(t0)
        out["t_bootcluster"] = t_b
        out["p_wcb"] = pw
    out.attrs.update(n_obs=n, k=k, k_eff=k_eff, n_clusters=G)
    return out, V
