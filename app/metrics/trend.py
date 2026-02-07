import numpy as np
from scipy.stats import linregress


def r2(close_series):
    if len(close_series) < 20:
        return 0

    x = np.arange(len(close_series))
    slope, intercept, r_value, _, _ = linregress(x, close_series)

    return r_value ** 2
