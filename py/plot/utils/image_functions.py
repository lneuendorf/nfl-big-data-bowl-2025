import matplotlib as mpl
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import Rectangle

def hex_to_rgb(hex_color):
    # Strip the '#' if it exists
    hex_color = hex_color.lstrip('#')
    
    # Convert hex to RGB
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def luminance(rgb: tuple) -> float:
    r, g, b = [x / 255.0 for x in rgb]  # Normalize to [0, 1]
    r = (r / 12.92) if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = (g / 12.92) if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = (b / 12.92) if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(hex_color1: str, hex_color2: str) -> float:
    rgb1 = hex_to_rgb(hex_color1)
    rgb2 = hex_to_rgb(hex_color2)
    
    lum1 = luminance(rgb1)
    lum2 = luminance(rgb2)
    
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)

def plot_image(
    ax: mpl.axes.Axes, 
    x:float, y:float, 
    imagebox:OffsetImage, 
    ord:int, 
    alignment='center',
) -> mpl.axes.Axes:
    """Helper function to add team logo to the plot."""
    if alignment == 'center':
        box_alignment=(0.5, 0.5)
    elif alignment == 'right-center':
        box_alignment=(1, 0.5)
    ab = AnnotationBbox(
        offsetbox=imagebox, 
        xy=(x, y),
        xybox=(0, 0),
        xycoords='data',
        boxcoords='offset points', 
        box_alignment=box_alignment,
        frameon=False,
        zorder=ord,
    )
    ax.add_artist(ab)

    return ax
