# %%
from typing import List, Tuple
import numpy as np
from scipy.stats import poisson

def get_rarity_labels() -> List[str]:
    """Get the list of rarity labels."""
    return [
        "Common",
        "Uncommon",
        "Rare",
        "Legendary",
        "Mythical",
        "N-F-Tacular",
        "Christmas Miracle"
    ]

def sample_rarity_level(week_num : int) -> int:
    """Sample a rarity level based on the PMF for this week!

    The week number is assumed to have been checked prior to calling this to ensure it is an integer between 0 and 4.

    The output is an integer index into the rarity label list.
    """
    # Grab the labels and IDs
    labels = get_rarity_labels()
    num_labels = len(labels)
    ids = np.arange(1, num_labels + 1)

    # Get the Poisson mean for this week
    mus = [1, 2, 6, 12, 16]
    mu = mus[week_num]

    # Compute the PMF over this support and normalize to ensure its still a distribution
    pmf = poisson.pmf(ids, mu=mu)
    pmf /= np.sum(pmf)

    # Sample from a categorical distribution
    samples = np.random.multinomial(n=1, pvals=pmf)
    return np.flatnonzero(samples)[0]

def sample_attributes(rarity_level: int) -> Tuple[int,...]:
    pass

def sample_frame(rarity_level: int) -> int:
    pass

# %%
