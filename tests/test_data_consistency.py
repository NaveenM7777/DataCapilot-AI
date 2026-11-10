import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(
    not (ROOT / "data" / "company_data.xlsx").exists()
    or not (ROOT / "data" / "company_doc.pdf").exists(),
    reason="company data files are not available",
)


@pytest.fixture(scope="module")
def spreadsheet():
    from excel_agent.data_loader import load_all_sheets

    sheets, error = load_all_sheets()
    assert error is None, error
    return sheets


@pytest.fixture(scope="module")
def pdf_text():
    from pdf_agent.pdf_loader import load_default_pdf

    full_text, _pages, _count, error = load_default_pdf()
    assert error is None, error
    return full_text


def number_after(label, text):
    """Finds the number printed right after a label, e.g. 'Total Units Sold 8,967'."""
    match = re.search(rf"{label}\s*\$?([\d,]+)", text)
    assert match, f"'{label}' was not found in the PDF"
    return int(match.group(1).replace(",", ""))


def test_total_revenue_matches_between_excel_and_pdf(spreadsheet, pdf_text):
    excel_value = int(spreadsheet["Monthly_Sales"]["Revenue"].sum())
    assert excel_value == number_after("Total Annual Revenue", pdf_text)


def test_total_units_match_between_excel_and_pdf(spreadsheet, pdf_text):
    excel_value = int(spreadsheet["Monthly_Sales"]["Units_Sold"].sum())
    assert excel_value == number_after("Total Units Sold", pdf_text)


def test_store_count_matches_between_excel_and_pdf(spreadsheet, pdf_text):
    excel_value = len(spreadsheet["Store_Locations"])
    assert excel_value == number_after("Number of Store Locations", pdf_text)


@pytest.mark.xfail(
    strict=True,
    reason="KNOWN DATA BUG: the PDF says 712 total new customers, the spreadsheet adds up to 732",
)
def test_total_new_customers_match_between_excel_and_pdf(spreadsheet, pdf_text):
    excel_value = int(spreadsheet["Monthly_Sales"]["New_Customers"].sum())
    assert excel_value == number_after("Total New Customers", pdf_text)