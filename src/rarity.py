# %%
from typing import List, Optional, Dict
import numpy as np
from scipy.stats import poisson
import random

def get_rarity_labels() -> List[str]:
    """Get the list of rarity labels."""
    return [
        "common",
        "uncommon",
        "rare",
        "legendary",
        "mythical",
        "n-f-tacular",
        "christmas miracle"
    ]

def rarity_label_to_level(rarity_label: str) -> int:
    """Convert a rarity label string to an integer level."""
    rarity_labels = get_rarity_labels()
    label_map = {f"{s}":i for i, s in enumerate(rarity_labels)}
    return label_map[rarity_label.lower()]

def rarity_level_to_label(rarity_level: int) -> str:
    """Convert a rarity level integer to an rarity label."""
    rarity_labels = get_rarity_labels()
    return rarity_labels[rarity_level]

def get_frame_names(rarity_label: str) -> Dict[str, List[Optional[str]]]:
    """Get a dictionary of frames keyed by the rarity label."""
    frame_map = {
        "common": [None],
        "uncommon": ["portal_blue","portal_orange"],
        "rare": ["darakge_red", "darkage_blue"],
        "legendary": ["darkage_rgb", "glitch_unstable"],
        "mythical": ["glitch_neon", "neon_frame", "glitch_wave"],
        "n-f-tacular": ["speedliness", "rain_of_gold", "cat_crime_graffiti"],
        "christmas miracle": ["christmas_lights"]
    }
    return frame_map[rarity_label.lower()]

def get_subjects(rarity_level: int) -> List[str]:
    """Get the list of subjects available to be sampled at a given rarity level."""
    subjects = [
        "cat",
        "dog",
        "monkey",
        "panda",
        "owl",
        "lion",
        "baby",
        "robot",
        "dragon",
        "reindeer",
        "santa claus",
    ]

    if rarity_level < 4:
        # Must be < Mythical
        return subjects[:5]

    if rarity_level < 6:
        # Must be Mythical to N-F-Tacular
        return subjects[:8]

    # Must be christmas miracle
    return subjects

def get_ages() -> List[Optional[str]]:
    """Get the list of possible ages."""
    return [None, "baby", "young", "old"]

def get_hats(rarity_level: int) -> List[Optional[str]]:
    """Get the list of hats available to be sampled at a given rarity level."""
    hats = [
        None,
        "winter hat",
        "nightcap",
        "beanie",
        "robot head",
        "santa hat",
        "party hat"
    ]

    if rarity_level < 5:
        # Must be < N-F-Tacular
        return hats[:2]
    
    if rarity_level < 6:
        # Must be < Christmas Miracle
        return hats[:4]
    
    # Must be Christmas Miracle
    return hats

def get_eyes(rarity_level: int) -> List[str]:
    """Get the list of eyes available to be sampled at a given rarity level."""
    eyes = [
        "white",
        "black",
        "blue",
        "brown",
        "green",
        "purple",
        "neon",
        "rgb",
        "rainbow",
        "fire",
        "sunglasses",
        "laser beam",
        "pepermint"
    ]

    if rarity_level < 4:
        # Must be < Mythical
        return eyes[:4]
    
    if rarity_level < 5:
        # Must be < N-F-Tacular
        return eyes[:7]
    
    if rarity_level < 6:
        # Must be < Christmas Miracle
        return eyes[:11]
    
    # Must be Christmas Miracle
    return eyes

def get_beards(rarity_level: int) -> List[Optional[str]]:
    """Get the list of beards available to be sampled at a given rarity level."""
    beards = [
        None,
        "white",
        "black",
        "blue",
        "brown",
        "green",
        "purple",
        "neon",
        "rgb",
        "rainbow",
        "fire",
        "pepermint"
    ]

    if rarity_level < 4:
        # Must be < Mythical
        return beards[:5]
    
    if rarity_level < 5:
        # Must be < N-F-Tacular
        return beards[:8]

    if rarity_level < 6:
        # Must be < Christmas Miracle
        return beards[:-1]

    # Must be Christmas Miracle
    return beards

def get_scarfs(rarity_level: int) -> List[Optional[str]]:
    """Get the list of scarfs available to be sampled at a given rarity level."""
    scarfs = [
        None,
        "white",
        "black",
        "blue",
        "brown",
        "green",
        "purple",
        "neon",
        "rgb",
        "rainbow",
        "fire",
        "pepermint"
    ]
    if rarity_level < 4:
        # Must be < Mythical
        return scarfs[:5]
    
    if rarity_level < 5:
        # Must be < N-F-Tacular
        return scarfs[:8]

    if rarity_level < 6:
        # Must be < Christmas Miracle
        return scarfs[:-1]

    # Must be Christmas Miracle
    return scarfs

def get_backgrounds(rarity_level: int) -> List[str]:
    """Get the list of backgrounds available to be sampled at a given rarity level."""
    backgorunds = [
        "snowy",
        "icey",
        "space",
        "fireplace",
        "christmas tree",
        "north pole"
    ]
    if rarity_level < 6:
        # Must be < Christmas Miracle
        return backgorunds[:2]
    # Must be Christmas Miracle
    return backgorunds

def get_styles() -> List[str]:
    """Get the list of possible artistic styles."""
    return ["realistic", "toon", "meme", "NFT"]

def get_pets() -> List[str]:
    """Return the list of pet names."""
    return [
        "butters",
        "jinx",
        "starfire",
        "patrick",
        "phillip",
        "winston",
        "allan",
        "nalla"
    ]

def sample_rarity_level(week_num : int) -> str:
    """Sample a rarity level based on the PMF for this week!

    The week number is assumed to have been checked prior to calling this to ensure it is an integer between 0 and 4.
    """
    # Grab the labels and IDs
    rarity_labels = get_rarity_labels()
    num_labels = len(rarity_labels)
    ids = np.arange(1, num_labels + 1)

    # Get the Poisson mean for this week
    mus = [1, 2, 6, 12, 16]
    mu = mus[week_num]

    # Compute the PMF over this support and normalize to ensure its still a distribution
    pmf = poisson.pmf(ids, mu=mu)
    pmf /= np.sum(pmf)

    # Sample from a categorical distribution
    samples = np.random.multinomial(n=1, pvals=pmf)
    rarity_level = np.flatnonzero(samples)[0]
    return rarity_level_to_label(rarity_level)

def sample_attributes(rarity_label: str) -> Dict[str, str]:
    """Sample the attributes based on the rarity level."""
    # Initialize the attributes dictionary
    attributes = {}

    # Get the rarity level
    rarity_level = rarity_label_to_level(rarity_label)

    # Set the rarity
    attributes["rarity"] = rarity_label

    # Sample the age
    ages = get_ages()
    age = random.choice(ages)
    attributes["age"] = age

    # Sample the subject
    subjects = get_subjects(rarity_level)
    subject = random.choice(subjects)
    attributes["subject"] = subject

    # Sample the beard
    beards = get_beards(rarity_level)
    beard = random.choice(beards)
    attributes["beard"] = beard

    # Sample the eyes
    eyes = get_eyes(rarity_level)
    eye = random.choice(eyes)
    attributes["eyes"] = eye

    # Sample the hat
    hats = get_hats(rarity_level)
    hat = random.choice(hats)
    attributes["hat"] = hat

    # Sample the scarfs
    scarfs = get_scarfs(rarity_level)
    scarf = random.choice(scarfs)
    attributes["scarf"] = scarf

    # Sample the background
    backgrounds = get_backgrounds(rarity_level)
    background = random.choice(backgrounds)
    attributes["background"] = background

    # Sample the style
    styles = get_styles()
    style = random.choice(styles)
    attributes["style"] = style

    return attributes

def sample_frame(rarity_label: str) -> str:
    """Sample a frame at this rarity level with equal probabilities."""
    fram_names = get_frame_names(rarity_label)
    return random.choice(fram_names)

# %%
