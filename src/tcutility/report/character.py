import os

from tcutility import cache, log


def _load_data() -> dict:
    """
    Load character width data. It is stored in a file where each line is formatted as:

            {font} {character} {width}

    Font names that originally contained spaces, for example "Times New Roman", will have the spaces replaced
    by underscores.

    Returns:
            We return a nested dictionary with the first key being the font and the nested key the characters.
            The widths are given in pixel sizes and are for font-size 1.
    """
    with open(os.path.join(os.path.split(__file__)[0], "_char_widths.txt"), encoding="utf-8") as widths:
        lines = widths.readlines()

    ret = {}
    for line in lines:
        # we split each line into parts by white space
        parts = line.split()
        # if there are only 2 parts, that means that the character was a space
        if len(parts) == 2:
            font, width = parts
            character = " "
        else:
            font, character, width = line.split()

        # fonts that contain spaces in the name had the spaces replaced by underscores
        # here we restore the original spaces
        font = font.replace("_", " ")
        width = float(width)

        ret.setdefault(font, {})
        ret[font][character] = width

    return ret


widths = _load_data()


@cache.cache
def get_pixel_width(character: str, font: str = "calibri", font_size: float = 11) -> float:
    """
    Get the pixel width of a character for a given font and font-size.
    For this we need to interpolate the pixel width between two reference values.
    In the _char_widths.txt file you will find for each font a set of character pixel widths for font-size 1.
    We then simply multiply the 1-width value by the desired value to get the correct pixel width.
    See

    Args:
            character: the character to get the pixel width for.
            font: the font family that is used.
            font_size: the font-size to get the pixel width at.
    """
    if font not in widths.keys():
        raise ValueError(f"Could not find font {font}.")

    return widths[font][character] * font_size


def text_width(text: str, font: str = "calibri", font_size: float = 11, mode: str = "pixels") -> float:
    """
    Get the width of a string for a given font and font size.

    Args:
            text: the object to determine the length for.
                    Will be cast to a string before calculating width.
            font: the font family that is used.
            font_size: the font-size to get the pixel width at.
            mode: the width-mode. Can be 'excel' or 'pixels'.

    Returns:
            The width of the text for a certain font and font size.
            If mode is 'excel' we pad it with 8 pixels and then divide by 7.6 (i.e. standard excel char width).
    """
    if font not in widths.keys():
        log.error(f"Could not find font {font}. Defaulting to Calibri.")
        font = "calibri"

    pixels = sum(get_pixel_width(char, font, font_size) for char in str(text))
    if mode == "excel":
        return (pixels + 8) / 7.6
    if mode == "word":
        return (pixels + 8) / 7.6

    return pixels


if __name__ == "__main__":
    print(text_width("this is a test text", font="test"))
