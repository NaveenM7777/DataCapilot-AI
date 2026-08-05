import os
import pandas as pd


DATA_FILE_PATH = os.path.join("data", "company_data.xlsx")


def get_file_modified_time():
    """Returns the file's last-modified timestamp, or None if it doesn't exist."""

    if not os.path.exists(DATA_FILE_PATH):
        return None

    return os.path.getmtime(DATA_FILE_PATH)


def load_default_data():
    """
    Loads the company spreadsheet fresh from disk. Called every time
    data is needed (not cached at startup), so updates to the file are
    picked up automatically without restarting the app.
    Returns (dataframe, sheet_names, error)
    """

    if not os.path.exists(DATA_FILE_PATH):
        return None, None, (
            f"Data file not found at '{DATA_FILE_PATH}'. "
            "Place your company spreadsheet there and restart the app."
        )

    try:
        filename = DATA_FILE_PATH.lower()

        if filename.endswith(".csv"):
            df = pd.read_csv(DATA_FILE_PATH)
            return df, None, None

        elif filename.endswith((".xlsx", ".xls")):

            excel_file = pd.ExcelFile(DATA_FILE_PATH)
            sheet_names = excel_file.sheet_names

            df = excel_file.parse(sheet_names[0])
            return df, sheet_names, None

        else:
            return None, None, "Unsupported file type in DATA_FILE_PATH. Use .csv or .xlsx."

    except Exception as e:
        return None, None, f"Failed to read file: {str(e)}"


def load_sheet_by_name(sheet_name):
    """Loads a specific sheet, fresh from disk."""

    try:
        excel_file = pd.ExcelFile(DATA_FILE_PATH)
        df = excel_file.parse(sheet_name)
        return df, None

    except Exception as e:
        return None, f"Failed to read sheet: {str(e)}"


def load_all_sheets():
    """
    Loads every sheet fresh from disk as a dict: {sheet_name: dataframe}.
    Used by the AI Agent, and always reflects the current file contents.
    """

    if not os.path.exists(DATA_FILE_PATH):
        return None, (
            f"Data file not found at '{DATA_FILE_PATH}'. "
            "Place your company spreadsheet there and restart the app."
        )

    try:
        excel_file = pd.ExcelFile(DATA_FILE_PATH)
        sheets = {name: excel_file.parse(name) for name in excel_file.sheet_names}
        return sheets, None

    except Exception as e:
        return None, f"Failed to read file: {str(e)}"