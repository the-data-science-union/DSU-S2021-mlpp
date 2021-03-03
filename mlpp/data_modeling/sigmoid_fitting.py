import scipy
from scipy.stats import norm
from scipy.optimize import curve_fit


def fit_normal_cdf(y):
    """Fits a set of cartesian points to the normal cdf

    Parameters
    ----------
    x (int []):  Array of point x-coordinates
    n_users (int): Array of point y-coordinates

    Returns
    -------
    params (tuple): Tuple of parameters for the normal cdf
    error (float): Mean squared error from points given
    """

    n = len(y)
    x = range(0, n)
    try:
        def f(x, mu, sigma): return scipy.stats.norm(mu, sigma).cdf(x)
        mu, sigma = scipy.optimize.curve_fit(f, x, y)[0]

    except RuntimeError:
        return "Error - curve_fit failed"

    total = 0
    for i in x:
        error = (y[i] - scipy.stats.norm(mu, sigma).cdf(i))**2
        total += error

    mse = total / n

    return (mu, sigma), mse


def fit_t_cdf(y):
    """Fits a set of cartesian points to the normal cdf

    Parameters
    ----------
    x (int []):  Array of point x-coordinates
    n_users (int): Array of point y-coordinates

    Returns

    params (tuple): Tuple of parameters for the normal cdf
    error (float): Least squares error from points given
    """

    x = range(len(y))
    try:
        def f(x, df): return scipy.stats.t(df).cdf(x)
        df = scipy.optimize.curve_fit(f, x, y)[0]

    except RuntimeError:
        return "Error - curve_fit failed"

    total = 0
    for i in x:
        error = (y[i] - scipy.stats.t(df).cdf(i))**2
        total += error

    mse = total / len(y)

    return df, mse

    pass
