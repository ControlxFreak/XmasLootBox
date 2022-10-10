# %%
"""
Rarity Level Statistics
=======================
The probability mass function (PMF) describing their rarity follows a sliding Poisson distribution.
Each week, the mean of the Poisson PMF will change from [1, 2, 6, 16].
The values of each rarity level remain fixed at 2 * [1,2,3,4,5,6,7,8].
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import poisson

# Initialization
labels = ["Common", "Uncommon", "Rare", "Legendary", "Mythical", "N-F-Tacular", "Christmas Miracle"]
num_labels = len(labels)
ids = np.arange(1, num_labels + 1)
values = 2*ids
mus = [1, 2, 6, 16]

# Compute the PMFs everyday
figi, axi = plt.subplots(nrows=4, ncols=1, sharex=True, figsize=(10, 15))
ipmfs = []
for wi, mu in enumerate(mus):
    # Grab the pmf for these IDs
    ipmf = poisson.pmf(ids, mu=mu)
    # Normalize to maintain distribution
    ipmf /= np.sum(ipmf)
    ipmfs.append(ipmf)
    # Print the values
    print(f"### Week {wi} Probabilities")
    print("| Level | Rarity (%) |")
    print("| ----------- | ----------- |")
    for l, p in zip(labels, ipmf):
        print(f"| {l} \t\t | {100 * p:.3f} % |")

    # Plot
    axi[wi].barh(labels, [100*p for p in ipmf])
    axi[wi].set_title(f"Week {wi + 1} Rarity Distribution")
    axi[wi].set_xlabel("Probability (%)")
    axi[wi].invert_yaxis()

os.makedirs("../docs/", exist_ok=True)
plt.tight_layout()
figi.savefig("../docs/rarity_histogram.png")

# %%
# Compute the probability that everyone gets at least 1 of each NFT rarity
probs = np.ones(num_labels)
for wi, ipmf in enumerate(ipmfs):
    # Compute the probability
    for i in range(num_labels):
        # Note there are 7 attempts per week
        probs[i] *= (1 - ipmf[i]) ** 7

# The probability of NOT getting it is 1 - probs
probs = 1 - probs
for l, p in zip(labels, probs):
    print(f"P(|{l}| > 1) = {100*p:.3f}")

# %%
