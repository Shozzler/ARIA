"""
Simple device type/category detection based on hostname keywords.

UniFi doesn't tell us what KIND of device a client is (phone, appliance,
TV, etc.) - but our devices already have descriptive hostnames, so we can
guess the category ourselves by looking for keywords in the name.
"""

# Maps a category name to a list of keywords we look for (case-insensitive)
# in the device's hostname. Order matters: the FIRST category with a match wins.
CATEGORY_KEYWORDS = {
    "Security": ["doorbell", "chime", "camera", "entrance"],
    "Appliance": ["fridge", "freezer", "oven", "gaggenau", "siemens", "bsp", "bop"],
    "Entertainment": ["tv", "webos", "nintendo", "switch"],
    "Mobile": ["iphone", "galaxy", "pixel", "ultra"],
    "Computer": ["laptop", "pc", "nas", "macbook"],
    "Network Equipment": ["tl-sg", "nano hd", "accesspoint"],
    "Home Comfort": ["purifier"],
}


def categorize_device(name: str) -> str:
    """
    Guess a device's category from its hostname.

    Args:
        name: The device's hostname/name (e.g. "Nintendo Switch OLED")

    Returns:
        A category string, or "Other" if nothing matched.
    """
    name_lower = name.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name_lower:
                return category

    return "Other"