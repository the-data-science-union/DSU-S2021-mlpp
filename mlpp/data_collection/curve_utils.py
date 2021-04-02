import numpy as np
from scipy.optimize import curve_fit

def linear_expon_fit(x, y, window_size = 0):
    b, a = np.polyfit(x, np.log(y), 1, w = np.sqrt(y))
    print(f'a:{a} b:{b}, e^(a + bx)')
    return lambda x: np.exp(a + b * (x + window_size))

def optimize_expon_fit(x, y, p0):
    def func(x, a, b, c):
        return a * np.power(b, c * x)
    
    popt, _ = curve_fit(func, x, y, p0 = p0)
    return lambda x: func(x, *popt)

def roll(x, y, window_size):
    if window_size < 2 or len(x) != len(y):
        print("Invalid params")
        return None
    
    def moving_average(x, w):
        return np.convolve(x, np.ones(w), 'valid') / w
    
    shift = int(window_size // 2)
    y1 = moving_average(y, window_size)
    x1 = x[shift : shift + len(y1)]

    return x1, y1


