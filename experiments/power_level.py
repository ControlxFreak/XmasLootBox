# %%
"""
Rarity Level Statistics
=======================
The probability mass function (PMF) describing their rarity follows a sliding Poisson distribution.
Each week, the mean of the Poisson PMF will change from [1, 2, 6, 16].
The values of each rarity level remain fixed at 2 * [1,2,3,4,5,6,7].
"""
import numpy as np
import matplotlib.pyplot as plt

bounds =[
    [00, 10],
    [10, 20],
    [20, 30]
]


# %%
