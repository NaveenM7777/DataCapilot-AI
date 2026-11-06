import re
import unicodedata

# Look-alike punctuation that models like to write -> the plain keyboard version
PUNCTUATION_MAP = str.maketrans(
    {
        "\u2010": "-",  # hyphen
        "\u2011": "-",  # non-breaking hyphen
        "\u2012": "-",  # figure dash
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2212": "-",  # minus sign
        "\u2018": "'",  # curly single quotes
        "\u2019": "'",
        "\u201c": '"',  # curly double quotes
        "\u201d": '"',
    }
)


def normalize(text):
    """
    Makes text safe to compare.
    Models often write 'invisible' look-alike characters: a non-breaking space
    inside 'New York', a non-breaking hyphen in 'ST-103', a curly apostrophe in
    "couldn't". NFKC fixes the spaces, the map fixes the punctuation, and then
    extra spaces are collapsed.
    """
    text = unicodedata.normalize("NFKC", text).translate(PUNCTUATION_MAP)
    return re.sub(r"\s+", " ", text).strip()


def numbers_in(text):
    return re.findall(r"\d+(?:\.\d+)?", normalize(text).replace(",", ""))


def contains_expected(expected, answer):
    """Numbers must appear as a number; words are matched ignoring case."""
    if re.fullmatch(r"\d+(?:\.\d+)?", expected):
        return expected in numbers_in(answer)
    return normalize(expected).lower() in normalize(answer).lower()