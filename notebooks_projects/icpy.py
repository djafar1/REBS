import itertools as it
from collections import namedtuple

import numpy as np
import scipy.stats
import sklearn.linear_model


def all_parent_sets(S, max_num_parents):
    return it.chain.from_iterable(
        it.combinations(S, n_parents) for n_parents in range(min(len(S), max_num_parents) + 1))


def f_test(x1, x2):
    """
    Perform F-test for equal variance.
    """
    F = np.var(x1, ddof=1) / np.var(x2, ddof=1)
    return 2 * min(scipy.stats.f.cdf(F, len(x1) - 1, len(x2) - 1), scipy.stats.f.sf(F, len(x1) - 1, len(x2) - 1))


def test_plausible_parent_set(X, y, z):
    """
    scipy.stats.ttest_ind:
    Calculate the T-test for the means of two independent samples of scores.
    This is a test for the null hypothesis that 2 independent samples have identical average (expected) values.
    This test assumes that the populations have identical variances by default.
    Parameters
    ----------
    X
    y
    z

    Returns
    -------

    """
    n_e = len(np.unique(z))
    environments = np.unique(z)
    lm = sklearn.linear_model.LinearRegression(fit_intercept=False)
    X_with_intercept = np.hstack((X, np.ones((X.shape[0], 1))))
    lm.fit(X_with_intercept, y)
    residuals = lm.predict(X_with_intercept) - y

    return min([2 * min(scipy.stats.ttest_ind(residuals[np.equal(z, e)],
                                              residuals[np.logical_not(np.equal(z, e))],
                                              equal_var=False).pvalue,
                        f_test(residuals[np.equal(z, e)],
                               residuals[np.logical_not(np.equal(z, e))]))
                for e in environments]) * n_e


def preselect_parents(X, y, n):
    _, selected, _ = sklearn.linear_model.lars_path(X, y, method='lasso', max_iter=n, return_path=False)
    return selected


ICP = namedtuple("ICP", ["S_hat", "q_values", "p_value"])


def invariant_causal_prediction(X, y, z, alpha=0.1):
    """
    Perform Invariant Causal Prediction.

    Parameters
    ----------
    X : (n, p) ndarray
        predictor variables
    y : (n,) ndarray
        target variable, numpy array of shape `(n)`
    z : array_like
        index of environment, length(Z)==`n`
    alpha : float
        Confidence level of the tests and FDR to control. :math:`P(\hat{S} \subset S^*) \geq 1-\mathtt{alpha}`

    Returns
    -------
    list
        The identified causal parent set, :math:`\hat{S}`, as list of indices

    """

    n = X.shape[0]
    p = X.shape[1]

    max_num_parents = 8

    S_0 = list(range(p))
    q_values = np.zeros(p)
    p_value_model = 0

    for S in all_parent_sets(S_0, max_num_parents):
        not_S = np.ones(p, bool)
        not_S[list(S)] = False
        p_value = test_plausible_parent_set(X[:, S], y, z)
        q_values[not_S] = np.maximum(q_values[not_S], p_value)
        p_value_model = max(p_value_model, p_value)

    q_values = np.minimum(q_values, 1)
    S_hat = np.where(q_values <= alpha)[0]
    return ICP(S_hat, q_values, p_value_model)


def fit_dataset(data, target):
    """

    Parameters
    ----------
    data: shape [environments, observations, variables]
    target_idx: int of max len(variables)
    target_idx

    Returns
    -------

    """
    if isinstance(data, list):
        data = np.array(data)

    z = []
    for k in range(data.shape[0]):
        for i in range(data.shape[1]):
            z.append(k)
    z = np.array(z)
    x = np.delete(data, target, axis=2).reshape((data.shape[0]*data.shape[1], data.shape[2]-1))
    y = data[:, :, target].reshape((data.shape[0]*data.shape[1], 1))
    return invariant_causal_prediction(x, y, z, alpha=0.1)


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
    result = fit_dataset(data, target=3)
    print(result)
