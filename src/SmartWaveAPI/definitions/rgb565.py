def colorRGB565(color: str) -> int:
    """Convert hex color to an RGB565 value.

    :return: this driver's color as an RGB565 value
    :rtype: int"""
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)

    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)