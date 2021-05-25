import scipy
from scipy.stats import norm
from scipy.optimize import curve_fit
import numpy as np
import matplotlib as plt
import pandas as pd


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

def makeArr(x):
    n=np.arange(0,x)
    return n

def algFunc(x, A, x0, k, off):
    f = A * (k*x - x0)/ (np.sqrt((k*x-x0)**2 + 1)) + off
    return f

def genLogFunc(x, A, K, B, Q, v):
    f = A + (K-A)/(1+Q*np.exp(-B*x)**(1/v))
    return f

def get_x_and_y(beatmap_id, db):
    
    beatmap = db['beatmap_criteria_curve'].find_one({'_id': beatmap_id})
    
    x_temp = np.arange(0,98)
    y_temp = np.asarray(beatmap['no_mod']['n_pass'])/np.asarray(beatmap['no_mod']['total'])
    y = y_temp[np.logical_not(np.isnan(y_temp))]
    x = makeArr(len(y))
   
    return x,y

def fit_alg(beatmap_id, db):
    while True:
        try:
            x = get_x_and_y(beatmap_id, db)[0]
            y = get_x_and_y(beatmap_id, db)[1]
            popt, pcov = curve_fit(algFunc, x, y, maxfev = 1000)
            popt=list(popt)
            return popt
        except RuntimeError:
            return None
        except TypeError:
            return None
    
def fit_genLog(beatmap_id, db):
    while True:
        try:
            x = get_x_and_y(beatmap_id, db)[0]
            y = get_x_and_y(beatmap_id, db)[1]
            popt, pcov = curve_fit(genLogFunc, x, y, maxfev = 1000)
            popt=list(popt)
            return popt
        except RuntimeError:
            return None
        except TypeError:
            return None
        
def plot_fit_alg(popt, beatmap_id, db, x, y):
    
    f, ax = plt.subplots(figsize = (14, 12))
    plt.title('Fitting algebraic function for beatmap %d' %(beatmap_id))
    plt.plot(x,y,label = 'original')
    plt.plot(x, algFunc(x, *popt), 'r-',label = 'Fitted logistic function')
    plt.legend()
    
def plot_fit_genLog(popt, beatmap_id):
    
    x = get_x_and_y(beatmap_id)[0]
    y = get_x_and_y(beatmap_id)[1]
    
    f, ax = plt.subplots(figsize = (14, 12))
    plt.title('Fitting generalized logistic function for beatmap %d' %(beatmap_id))
    plt.plot(x,y,label = 'original')
    plt.plot(x, genLogFunc(x, *popt), 'r-',label = 'Fitted logistic function')
    plt.legend()
    
def mse_alg(beatmap_id, db):
    while True:
        try:
            x = get_x_and_y(beatmap_id, db)[0]
            y = get_x_and_y(beatmap_id, db)[1]
            popt, pcov = curve_fit(algFunc, x, y, maxfev = 1000)
            mse = np.mean((y-algFunc(x, *popt))**2)
            return mse
        except RuntimeError:
            return None
        except TypeError:
            return None

def mse_genLog(beatmap_id, db):
    while True:
        try:
            x = get_x_and_y(beatmap_id, db)[0]
            y = get_x_and_y(beatmap_id, db)[1]
            popt, pcov = curve_fit(genLogFunc, x, y, maxfev = 1000)
            mse = np.mean((y-genLogFunc(x, *popt))**2)
            return mse
        except RuntimeError:
            return None
        except TypeError:
            return None

def genLogSuccess(idList, db):
    success = 0
    for el in idList:
        if fit_genLog(el, db):
            success += 1
    success_rate = success / len(idList)
    return success_rate

def algSuccess(idList, db):
    success = 0
    for el in idList:
        if fit_alg(el, db):
            success += 1
    success_rate = success / len(idList)
    return success_rate

def genLogAverageMse(idList, db):
    totalMse = 0
    success = 0
    for el in idList:
        if mse_genLog(el, db):
            totalMse += mse_genLog(el, db)
            success += 1
    avgMse = totalMse / success
    return avgMse

def algAverageMse(idList, db):
    totalMse = 0
    success = 0
    for el in idList:
        if mse_alg(el, db):
            totalMse += mse_alg(el, db)
            success += 1
    avgMse = totalMse / success
    return avgMse

def fit_all(db):
    cursor = db["beatmap_criteria_curve"].find({},{"_id":1})
    l = []
    for el in cursor:
        l.append(el)
    Ids = list(map(lambda x: x["_id"], l))
    global genLogSuccessAll
    global algSuccessAll
    global genLogAverageMseAll
    global algAverageMseAll
    genLogSuccessAll = genLogSuccess(Ids, db)
    algSuccessAll = algSuccess(Ids, db)
    genLogAverageMseAll = genLogAverageMse(Ids, db)
    algAverageMseAll = algAverageMse(Ids, db)
    
    return [genLogSuccessAll, algSuccessAll, genLogAverageMseAll, algAverageMseAll]

def fit_lowDiff(db):
    collection = db["attrib_17"]
    cursor = db.attrib_17.aggregate([
        {"$match" : {"value" : {"$gte" : 1, "$lt": 4}}},
        {"$project" : {"beatmap_id" : "$beatmap_id"}}
    ])
    l = list(cursor)
    lowIds = list(map(lambda x: x["beatmap_id"], l))
    global genLogSuccessLow
    global algSuccessLow
    global genLogAverageMseLow
    global algAverageMseLow
    genLogSuccessLow = genLogSuccess(lowIds, db)
    algSuccessLow = algSuccess(lowIds, db)
    genLogAverageMseLow = genLogAverageMse(lowIds, db)
    algAverageMseLow = algAverageMse(lowIds, db)
    
    return [genLogSuccessLow, algSuccessLow, genLogAverageMseLow, algAverageMseLow]

def fit_mediumDiff(db):
    cursor = db.attrib_17.aggregate([
        {"$match" : {"value" : {"$gte" : 4, "$lt": 6}}},
        {"$project" : {"beatmap_id" : "$beatmap_id"}}
    ])
    l = list(cursor)
    mediumIds = list(map(lambda x: x["beatmap_id"], l))
    global genLogSuccessMedium
    global algSuccessMedium
    global genLogAverageMseMedium
    global algAverageMseMedium
    genLogSuccessMedium = genLogSuccess(mediumIds, db)
    algSuccessMedium = algSuccess(mediumIds, db)
    genLogAverageMseMedium = genLogAverageMse(mediumIds, db)
    algAverageMseMedium = algAverageMse(mediumIds, db)

    return [genLogSuccessMedium, algSuccessMedium, genLogAverageMseMedium, algAverageMseMedium]

def fit_highDiff(db):
    cursor = db.attrib_17.aggregate([
        {"$match" : {"value" : {"$gte" : 6}}},
        {"$project" : {"beatmap_id" : "$beatmap_id"}}
    ])

    l = list(cursor)
    highIds = list(map(lambda x: x["beatmap_id"], l))
    global genLogSuccessHigh
    global algSuccessHigh
    global genLogAverageMseHigh
    global algAverageMseHigh
    genLogSuccessHigh = genLogSuccess(highIds, db)
    algSuccessHigh = algSuccess(highIds, db)
    genLogAverageMseHigh = genLogAverageMse(highIds, db)
    algAverageMseHigh = algAverageMse(highIds, db)

    return [genLogSuccessHigh, algSuccessHigh, genLogAverageMseHigh, algAverageMseHigh]

def store_genLog(Ids, db):
    for el in Ids: 
        if fit_genLog(el, db):
            success = True
        else: success = False
    
        db.beatmap_criteria_curve.update_one( 
            {"_id" : el},
            {"$set": {"no_mod.mlpp.genLogistic.success" : success,
                      "no_mod.mlpp.genLogistic.params" : fit_genLog(el, db),
                      "no_mod.mlpp.genLogistic.mse" : mse_genLog(el, db)}})
def store_alg(Ids, db):
    for el in Ids: 
        if fit_alg(el, db):
            success = True
        else: success = False
    
        db.beatmap_criteria_curve.update_one( 
            {"_id" : el},
            {"$set": {"no_mod.mlpp.algebraic.success" : success,
                      "no_mod.mlpp.algebraic.params" : fit_alg(el, db),
                      "no_mod.mlpp.algebraic.mse" : mse_alg(el, db)}})

