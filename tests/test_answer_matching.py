import pytest

from answer_matching import contains_expected, normalize, numbers_in


@pytest.mark.parametrize(
    "answer",
    [
        "The oldest store is New York.",
        "The oldest store is New\u00a0York.",   # non-breaking space
        "The oldest store is New\u202fYork.",   # narrow non-breaking space
        "The oldest store is NEW   YORK.",      # extra spaces and capitals
    ],
    ids=["plain", "nbsp", "narrow-nbsp", "spaces-and-case"],
)
def test_words_match_despite_invisible_characters(answer):
    assert contains_expected("New York", answer)


def test_non_breaking_hyphen_is_normalized():
    assert normalize("ST\u2011103") == "ST-103"


def test_curly_apostrophe_is_normalized():
    assert normalize("I couldn\u2019t find it") == "I couldn't find it"


def test_numbers_ignore_commas_and_currency():
    assert "272500" in numbers_in("Total revenue was $272,500 (Page 1).")


def test_number_must_be_a_whole_number_not_part_of_another():
    assert not contains_expected("5", "There are 59 customers.")


def test_wrong_words_do_not_match():
    assert not contains_expected("New York", "The oldest store is Toronto.")