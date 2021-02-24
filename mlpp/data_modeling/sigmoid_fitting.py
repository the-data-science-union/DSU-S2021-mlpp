def fit_normal_cdf(bm_total, y):

    """Fits a set of cartesian points to the normal cdf

    Parameters
    ----------
    x (int []):  Array of point x-coordinates
    n_users (int): Array of point y-coordinates

    Returns
    -------
    params (tuple): Tuple of parameters for the normal cdf
    error (float): Least squares error from points given
    """
    import scipy
    
    def helper_take_out_zero(bm_total):
        good_index = []
        k = 0
        for total in bm_total: 
            if (total != 0):
                good_index.append(k)
            k = k + 1
        bm_good_total = [bm_total[i] for i in good_index]
        return bm_good_total

    x = range(0, len(helper_take_out_zero(bm_total)))
    
    f = lambda x, mu,sigma: scipy.stats.norm(mu,sigma).cdf(x)
    mu,sigma = scipy.optimize.curve_fit(f, x, y)[0]

    total = 0
    for i in x:
        error = (y[i] - scipy.stats.norm(mu,sigma).cdf(i))**2
        total += error
    
    mse = total / n
    
    return scipy.stats.norm(mu,sigma).cdf(x), mse

    pass

def fit_logistic(x, y):
    """Fits a set of cartesian points to the logistic function

    Parameters
    ----------
    x (int []):  Array of point x-coordinates
    n_users (int): Array of point y-coordinates

    Returns
    -------
    params (tuple): Tuple of parameters for the logistic function
    error (float): Least squares error from points given
    """
    
    pass
