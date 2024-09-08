
def is_lower_eq(value, threshold):
    """
    Check if `value` is less than or equal to `threshold`.
    `threshold` of `None` means no threshold.
    """
    return threshold is None or value <= threshold