"""This module contains the implementation of the Invariant Causal
Prediction algorithm (see icp.fit).
"""

import numpy as np
import itertools
from termcolor import colored
from causalicp.data import _Data
import scipy.stats  # For t-test and f-test


# ---------------------------------------------------------------------
# "Public" API: fit function

def fit(data, target, alpha=0.05, sets=None, precompute=True, verbose=False, color=True):
    """Run Invariant Causal Prediction on data from different experimental
    settings.

    Parameters
    ----------
    data : numpy.ndarray or list of array-like
        The data from all experimental settings. Each element of the
        list/array is a 2-dimensional array with a sample from a
        different setting, where columns correspond to variables and
        rows to observations (data-points). The data also contains the
        response variable, which is specified with the `target`
        parameter.
    target : int
        The index of the response or target variable of interest.
    alpha : float, default=0.05
        The level of the test procedure, taken from `[0,1]`. Defaults
        to `0.05`.
    sets : list of set or None, default=None
        The sets for which ICP will test invariance. An error is
        raised if a set is not a subset of `{0,...,p-1}` or it
        contains the target, where `p` is the total number of
        variables (including the target). If `None` all possible
        subsets of predictors will be considered.
    precompute : bool, default=True
        Wether to precompute the sample covariance matrix to speed up
        linear regression during the testing of each predictor
        set. For large sample sizes this drastically reduces the
        overall execution time, but it may result in numerical
        instabilities for highly correlated data. If set to `False`,
        for each set of predictors the regression is done using an
        iterative least-squares solver on the raw data.
    verbose: bool, default=False
        If ICP should run in verbose mode, i.e. displaying information
        about completion and the result of tests.
    color : bool, default=True
        If the output produced when `verbose=True` should be color
        encoded (not recommended if your terminal does not support
        ANSII color formatting), see
        `termcolor <https://pypi.org/project/termcolor/>`__.

    Raises
    ------
    ValueError :
        If the value of some of the parameters is not appropriate,
        e.g. `alpha` is negative, `data` contains samples with
        different number of variables, or `sets` contains invalid
        sets.
    TypeError :
        If the type of some of the parameters was not expected (see
        examples below).

    Returns
    -------
    result : causalicp.Result
        A :class:`causalicp.Result` object containing the result of
        running ICP, i.e. estimate, accepted sets, p-values, etc.
    """
    # Check inputs: alpha
    if not isinstance(alpha, float):
        raise TypeError("alpha must be a float, not %s." % type(alpha))
    if alpha < 0 or alpha > 1:
        raise ValueError("alpha must be in [0,1].")

    # Check inputs: data
    data = _Data(data, method='scatter' if precompute else 'raw')

    # Check inputs: target
    if not isinstance(target, int):
        raise TypeError("target must be an int, not %s." % type(target))
    if target < 0 or target >= data.p or int(target) != target:
        raise ValueError("target must be an integer in [0, p-1].")

    # Check inputs: precompute
    if not isinstance(precompute, bool):
        raise TypeError("precompute must be bool, not %s." % type(precompute))

    # Check inputs: verbose
    if not isinstance(verbose, bool):
        raise TypeError("verbose must be bool, not %s." % type(verbose))

    # Check inputs: color
    if not isinstance(color, bool):
        raise TypeError("color must be bool, not %s." % type(color))

    # Check inputs: sets
    base = set(range(data.p))
    base -= {target}
    # If sets is provided, check its validity
    if sets is not None:
        if not isinstance(sets, list):
            raise TypeError("sets must be a list of set, not %s." % type(sets))
        else:
            for s in sets:
                if not isinstance(s, set):
                    raise TypeError("sets must be a list of set, not of %s." % type(s))
                elif len(s - base) > 0:
                    raise ValueError(
                        "Set %s in sets is not valid: it must be a subset of {0,...,p-1} - {target}." % s)
        candidates = sets
    # Build set of candidate sets
    else:
        # max_predictors = data.p - 1 if max_predictors is None else max_predictors
        max_predictors = data.p - 1
        if max_predictors > 8:
            max_predictors = 8
        candidates = []
        for set_size in range(max_predictors + 1):
            candidates += list(itertools.combinations(base, set_size))

    # ----------------------------------------------------------------
    # Evaluate candidate sets
    accepted = []  # To store the accepted sets
    rejected = []  # To store the sets that were rejected
    confidence_intervals = []
    p_values = {}  # To store the p-values of the tested sets
    coefficients = {}  # To store the estimated coefficients of the tested sets
    estimate = base
    print("Tested sets and their p-values:") if verbose else None
    # Test each set
    for S in candidates:
        S = set(S)
        # Test hypothesis of invariance
        reject, conf_interval, p_value, coefs = _test_hypothesis(target, S, data, alpha)
        # Store result appropriately and update estimate (if necessary)
        p_values[tuple(S)] = p_value
        coefficients[tuple(S)] = coefs
        if not reject:
            confidence_intervals.append(conf_interval)
            accepted.append(S)
            estimate &= S  # set intersection
        if reject:
            rejected.append(S)
        # Optionally, print output
        if verbose:
            set_str = 'rejected' if reject else 'accepted'
            if color:
                color = 'red' if reject else 'green'
                msg = colored('  %s %s : %s' % (S, set_str, p_value), color)
            else:
                msg = '  %s %s : %s' % (S, set_str, p_value)
            print(msg)
    # If no sets are accepted, there is a model violation. Reflect
    # this by setting the estimate to None
    if len(accepted) == 0:
        estimate = None
    print("Estimated parental set: %s" % estimate) if verbose else None
    # Create and return the result object
    result = Result(target,
                    data,
                    estimate,
                    accepted,
                    rejected,
                    confidence_intervals,
                    p_values,
                    coefficients)
    return result


# --------------------------------------------------------------------
# Auxiliary (private) functions

def _test_hypothesis(y, S, data, alpha):
    """Test the hypothesis for the invariance of the set S for the
    target/response y"""
    # Compute pooled coefficients and environment-wise residuals
    coefs, intercept = data.regress_pooled(y, S)
    residuals = data.residuals(y, coefs, intercept)
    # Build p-values for the hypothesis that error distribution
    # remains invariant in each environment
    mean_pvalues = np.zeros(data.e)
    var_pvalues = np.zeros(data.e)
    for i in range(data.e):
        residuals_i = residuals[i]
        residuals_others = np.hstack([residuals[j] for j in range(data.e) if j != i])
        mean_pvalues[i] = _t_test(residuals_i, residuals_others)
        var_pvalues[i] = _f_test(residuals_i, residuals_others)
    # Combine p-values via bonferroni correction
    smallest_pvalue = min(min(mean_pvalues), min(var_pvalues))
    p_value = min(1, smallest_pvalue * 2 * (data.e - 1))  # The -1 term is from the R implementation
    reject = p_value <= alpha
    # If set is accepted, compute confidence intervals
    if reject:
        return reject, None, p_value, (coefs, intercept)
    else:
        conf_ints = _confidence_intervals(y, coefs, S, residuals, alpha, data)
        return reject, conf_ints, p_value, (coefs, intercept)


def _t_test(X, Y):
    """Return the p-value of the two sample t-test for the given samples."""
    result = scipy.stats.ttest_ind(X, Y, equal_var=False)
    return result.pvalue


def _f_test(X, Y):
    """Return the p-value of the two-sided f-test for the given samples."""
    F = np.var(X, ddof=1) / np.var(Y, ddof=1)
    p = scipy.stats.f.cdf(F, len(X) - 1, len(Y) - 1)
    return 2 * min(p, 1 - p)


def _confidence_intervals(y, coefs, S, residuals, alpha, data):
    """Compute the confidence intervals for the coefficients estimated for
    a set S for the target/response y"""
    # NOTE: This is done following the R implementation. The paper
    # suggests a different approach using the t-distribution.
    # NOTE: `residuals` could be recomputed from `y, data, coefs`; but
    # why waste compute time
    lo = np.zeros(data.p)
    hi = np.zeros(data.p)
    # No need to compute intervals for the empty set
    if len(S) == 0:
        return (lo, hi)
    # Compute individual terms
    S = list(S)
    # 1.1. Estimate residual variance
    residuals = np.hstack(residuals)
    sigma = residuals @ residuals / (data.N - len(S) - 1)
    # 1.2. Estimate std. errors of the coefficients
    sup = S + [data.p]  # Must include intercept in the computation
    correlation = data.pooled_correlation[:, sup][sup, :]
    corr_term = np.diag(np.linalg.inv(correlation))
    std_errors = np.sqrt(sigma * corr_term)[:-1]
    # 2. Quantile term
    quantile = scipy.stats.norm.ppf(1 - alpha / 4)
    # All together
    delta = quantile * std_errors
    lo[S] = coefs[S] - delta
    hi[S] = coefs[S] + delta
    return (lo, hi)


class Result():
    """The result of running Invariant Causal Prediction, produced as
    output of :meth:`causalicp.fit`.

    Attributes
    ----------
    p : int
        The total number of variables in the data (including the response/target).
    target : int
        The index of the response/target.
    estimate : set or None
        The estimated parental set returned by ICP, or `None` if all
        sets of predictors were rejected.
    accepted_sets : list of set
        A list containing the accepted sets of predictors.
    rejected_sets : list of set
        A list containing the rejected sets of predictors.
    pvalues : dict of (int, float)
        A dictionary containing the p-value for the causal effect of
        each individual predictor. The target/response is included in
        the dictionary and has value `nan`.
    conf_intervals : numpy.ndarray or None
        A `2 x p` array of floats representing the confidence interval
        for the causal effect of each variable. Each column
        corresponds to a variable, and the first and second row
        correspond to the lower and upper limit of the interval,
        respectively. The column corresponding to the target/response
        is set to `nan`.
    """

    def __init__(self, target, data, estimate, accepted, rejected, conf_intervals, set_pvalues, set_coefs):
        # Save details of setup
        self.p = data.p
        self.target = target

        # Store estimate, sets, set pvalues and coefficients
        self.estimate = estimate if len(accepted) > 0 else None
        self.accepted_sets = sorted(accepted)
        self.rejected_sets = sorted(rejected)

        # Compute p-values for individual variables
        if len(accepted) == 0:
            # If all sets are rejected, set the p-value of all
            # variables to 1
            self.pvalues = dict((j, 1) for j in range(self.p))
            self.pvalues[target] = np.nan
        else:
            # Otherwise, the p-value of each variable is the highest
            # among the p-values of the sets not containing j
            self.pvalues = {}
            for j in range(self.p):
                if j == target:
                    self.pvalues[j] = np.nan
                else:
                    # p-values of sets not containing j
                    not_j = [pval for S, pval in set_pvalues.items() if j not in S]
                    self.pvalues[j] = max(not_j)

        # Compute confidence intervals
        if len(accepted) == 0:
            self.conf_intervals = None
        else:
            mins = np.array([i[0] for i in conf_intervals])
            maxs = np.array([i[1] for i in conf_intervals])
            self.conf_intervals = np.array([mins.min(axis=0), maxs.max(axis=0)])
            self.conf_intervals[:, target] = np.nan

        # Coefficients?
        # if len(accepted) == 0:
        #     self.coefficients = None
        # else:
        #     self.coefficients = {}
        #     res_coef = {}
        #     for x in self.estimate:
        #         res_coef[x] = []
        #
        #     for tpl, (coef,intercept) in set_coefs.items():
        #         for x in tpl:
        #             if x in self.estimate:
        #                 res_coef[x].append(coef[x])
        #     for k,v in res_coef.items():
        #         self.coefficients[k] = np.mean(v)


if __name__ == '__main__':
    data = [np.array([[0.46274901, -0.19975643, 0.76993618, 2.65949677],
                      [0.3749258, -0.98625196, -0.1806925, 1.23991796],
                      [-0.39597772, -1.79540294, -0.39718702, -1.31775062],
                      [2.39332284, -3.22549743, 0.15317657, 1.60679175],
                      [-0.56982823, 0.5084231, 0.41380479, 1.19607095]]),
            np.array([[1.45648798, 8.29977262, 1.05992289, 7.49191164],
                      [-1.35654212, 13.59077259, -1.14624494, 5.76580633],
                      [-0.48800913, 11.15112687, 0.48421499, 7.20695569],
                      [2.74901219, 8.82465628, 1.49619723, 12.48016441],
                      [5.35033726, 12.91847915, 1.69812062, 19.40468998]]),
            np.array([[-11.73619893, -6.87502658, -6.71775898, -28.2782561],
                      [-16.24118216, -11.26774231, -9.22041168, -42.09076079],
                      [-14.85266731, -11.02688079, -8.71264951, -40.37471919],
                      [-16.08519052, -11.73497156, -10.58198058, -42.55646184],
                      [-17.07817707, -11.29005529, -10.04063011, -45.01702447]])]

    result = fit(data, 3, alpha=0.05, precompute=True, verbose=True, color=False)
