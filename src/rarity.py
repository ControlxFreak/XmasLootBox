# %%
from typing import List, Optional, Dict
from math import factorial
import numpy as np
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
        "christmas miracle",
    ]


def get_short_rarity_labels() -> List[str]:
    """Get the list of rarity labels (shortend)."""
    return [
        "com",
        "uncom",
        "rare",
        "leg",
        "myth",
        "nftac",
        "miracle",
    ]


def rarity_label_to_level(rarity_label: str) -> int:
    """Convert a rarity label string to an integer level."""
    rarity_labels = get_rarity_labels()
    label_map = {f"{s}": i for i, s in enumerate(rarity_labels)}
    return label_map[rarity_label.lower()]


def rarity_level_to_label(rarity_level: int) -> str:
    """Convert a rarity level integer to an rarity label."""
    rarity_labels = get_rarity_labels()
    return rarity_labels[rarity_level]


def get_rarity_color(rarity_label: str) -> hex:
    """Convert a rarity label string to its corresponding hex color."""
    color_map = {
        "common": 0x808080,  # Grey
        "uncommon": 0x00873E,  # Green
        "rare": 0x4056AA,  # Blue
        "legendary": 0xA020F0,  # Purple
        "mythical": 0xFFFF00,  # Yellow
        "n-f-tacular": 0xFFA500,  # Orange
        "christmas miracle": 0xC54245,  # Christmas Red
    }
    return color_map[rarity_label]


def get_frame_names(rarity_label: str) -> Dict[str, List[Optional[str]]]:
    """Get a dictionary of frames keyed by the rarity label."""
    frame_map = {
        "common": [None],
        "uncommon": ["portal_blue", "portal_orange"],
        "rare": ["darkage_red", "darkage_blue"],
        "legendary": ["darkage_rgb", "glitch_unstable"],
        "mythical": ["glitch_neon", "neon_frame", "glitch_wave"],
        "n-f-tacular": ["speedlines", "rain_of_gold", "cat_crime_graffiti", "astro"],
        "christmas miracle": ["christmas_lights", "holiday", "mapplestory"],
    }
    return frame_map[rarity_label.lower()]


def get_subjects(rarity_level: int) -> List[str]:
    """Get the list of subjects available to be sampled at a given rarity level."""
    subjects = [
        "cat",
        "dog",
        "monkey",
        "panda",
        "fox",
        "owl",
        "lion",
        "robot",
        "dino",
        "dragon",
        "reindeer",
        "santa claus",
    ]

    if rarity_level < 3:
        # Must be < Legendary
        return subjects[:6]

    if rarity_level < 6:
        # Must be anything but christmas miracle
        return subjects[:9]

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
        "party hat",
    ]

    if rarity_level < 5:
        # Must be < N-F-Tacular
        return hats[:3]

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
        "peppermint",
    ]

    if rarity_level < 4:
        # Must be < Mythical
        return eyes[:5]

    if rarity_level < 5:
        # Must be < N-F-Tacular
        return eyes[:7]

    if rarity_level < 6:
        # Must be < Christmas Miracle
        return eyes[:11]

    # Must be Christmas Miracle
    return eyes


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
        "peppermint",
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


def get_sweaters(rarity_level: int) -> List[Optional[str]]:
    """Get the list of sweaters available to be sampled at a given rarity level."""
    sweaters = [
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
        "peppermint",
    ]
    if rarity_level < 4:
        # Must be < Mythical
        return sweaters[:5]

    if rarity_level < 5:
        # Must be < N-F-Tacular
        return sweaters[:8]

    if rarity_level < 6:
        # Must be < Christmas Miracle
        return sweaters[:-1]

    # Must be Christmas Miracle
    return sweaters


def get_backgrounds() -> List[str]:
    """Get the list of backgrounds available to be sampled at a given rarity level."""
    backgrounds = [
        "snowy",
        "icey",
        "space",
        "fireplace",
        "christmas tree",
        "north pole",
    ]
    return backgrounds


def get_styles() -> List[str]:
    """Get the list of possible artistic styles."""
    return [
        "cartoon",
        "NFT",
        "pixel",
        "cute",
        "anime",
        "fantasy",
        "digital painting",
        "digital art",
        "cyberpunk digital art",
        "steampunk digital art",
        "watercolor",
        "child's drawing",
        "crayon",
        "low poly",
        "sticker illustration",
        "storybook",
        "3D render",
        "vintage Disney",
        "Pixar",
        "Studio Ghibli",
        "South Park",
        "Simpsons",
        "Adventure Time",
        "vector art",
    ]


def get_rarity_pmf(week_num: int) -> str:
    """Get the rarity pmf for this week."""
    # Grab the labels and IDs
    rarity_labels = get_rarity_labels()
    num_labels = len(rarity_labels)
    ids = np.arange(1, num_labels + 1)

    # Get the Poisson mean for this week
    mus = [1, 2, 6, 12, 16]
    mu = mus[week_num]
    exp_mu = np.exp(-mu)

    # Compute the PMF over this support and normalize to ensure its still a distribution
    pmf = [(exp_mu * (mu**i)) / factorial(i) for i in ids]
    pmf /= np.sum(pmf)
    return pmf


def sample_rarity_label(week_num: int) -> str:
    """Sample a rarity label based on the PMF for this week!

    The week number is assumed to have been checked prior to calling this to ensure it is an integer between 0 and 4.
    """
    pmf = get_rarity_pmf(week_num)
    samples = np.random.multinomial(n=1, pvals=pmf)
    rarity_level = np.flatnonzero(samples)[0]
    return rarity_level_to_label(rarity_level)


def sample_rarity_label_uniform() -> str:
    """Sample a rarity label according to a uniform distribution."""
    # Grab the labels and IDs
    rarity_labels = get_rarity_labels()
    p = [1 / 48, 2 / 48, 2 / 48, 6 / 48, 12 / 48, 12 / 48, 13 / 48]
    return np.random.choice(rarity_labels, p=p)


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

    # Sample the sweater
    sweaters = get_sweaters(rarity_level)
    sweater = random.choice(sweaters)
    attributes["sweater"] = sweater

    # Sample the background
    backgrounds = get_backgrounds()
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
