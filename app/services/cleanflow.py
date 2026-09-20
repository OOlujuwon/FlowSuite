from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}


def normalize_column_name(name: Any) -> str:
    """Convert a column name into a clean, consistent format."""
    text = str(name).strip()
    text = " ".join(text.split())

    replacements = {
        " ": "_",
        "-": "_",
        "/": "_",
        "\\": "_",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.lower()


def load_dataframe(
    filename: str,
    file_bytes: bytes,
) -> pd.DataFrame:
    """Load a CSV or XLSX file into a DataFrame."""
    filename_lower = filename.lower()

    if filename_lower.endswith(".csv"):
        return pd.read_csv(BytesIO(file_bytes))

    if filename_lower.endswith(".xlsx"):
        return pd.read_excel(BytesIO(file_bytes))

    raise ValueError(
        "Unsupported file type. Please upload a CSV or XLSX file."
    )


def clean_dataframe(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """
    Clean a DataFrame and return:
    (cleaned_dataframe, cleaning_summary)
    """
    original_rows = len(df)
    original_columns = len(df.columns)

    working = df.copy()

    # ---------------------------------------------------------
    # 1. Normalize column names.
    # ---------------------------------------------------------

    original_column_names = list(working.columns)

    normalized_columns = [
        normalize_column_name(column)
        for column in working.columns
    ]

    # Make duplicate column names unique.
    seen: dict[str, int] = {}
    unique_columns = []

    for column in normalized_columns:
        count = seen.get(column, 0)

        if count == 0:
            unique_columns.append(column)
        else:
            unique_columns.append(
                f"{column}_{count}"
            )

        seen[column] = count + 1

    working.columns = unique_columns

    columns_changed = sum(
        old != new
        for old, new in zip(
            original_column_names,
            working.columns,
        )
    )

    # ---------------------------------------------------------
    # 2. Clean text cells.
    #
    # Strip leading/trailing whitespace and normalize whitespace
    # inside text values.
    # ---------------------------------------------------------

    whitespace_cells_cleaned = 0

    for column in working.columns:
        if not (
            pd.api.types.is_object_dtype(working[column])
            or pd.api.types.is_string_dtype(working[column])
        ):
            continue

        for index in working.index:
            value = working.at[index, column]

            if pd.isna(value):
                continue

            if not isinstance(value, str):
                continue

            cleaned_value = " ".join(value.split())

            if cleaned_value != value:
                whitespace_cells_cleaned += 1

            working.at[index, column] = cleaned_value

    # ---------------------------------------------------------
    # 3. Convert empty strings to missing values.
    # ---------------------------------------------------------

    blank_values_replaced = 0

    for column in working.columns:
        if not (
            pd.api.types.is_object_dtype(working[column])
            or pd.api.types.is_string_dtype(working[column])
        ):
            continue

        blank_mask = working[column].map(
            lambda value: (
                isinstance(value, str)
                and value == ""
            )
        )

        blank_values_replaced += int(
            blank_mask.sum()
        )

        working.loc[
            blank_mask,
            column,
        ] = pd.NA

    # ---------------------------------------------------------
    # 4. Remove completely empty rows.
    # ---------------------------------------------------------

    before_empty_rows = len(working)

    working = (
        working
        .dropna(how="all")
        .reset_index(drop=True)
    )

    empty_rows_removed = (
        before_empty_rows - len(working)
    )

    # ---------------------------------------------------------
    # 5. Remove duplicate rows.
    # ---------------------------------------------------------

    before_duplicates = len(working)

    working = (
        working
        .drop_duplicates(keep="first")
        .reset_index(drop=True)
    )

    duplicate_rows_removed = (
        before_duplicates - len(working)
    )

    # ---------------------------------------------------------
    # 6. Build summary.
    # ---------------------------------------------------------

    total_changes = (
        columns_changed
        + whitespace_cells_cleaned
        + blank_values_replaced
        + empty_rows_removed
        + duplicate_rows_removed
    )

    summary = {
        "original_rows": original_rows,
        "cleaned_rows": len(working),
        "original_columns": original_columns,
        "cleaned_columns": len(working.columns),
        "columns_renamed": columns_changed,
        "whitespace_cells_cleaned": whitespace_cells_cleaned,
        "blank_values_replaced": blank_values_replaced,
        "empty_rows_removed": empty_rows_removed,
        "duplicate_rows_removed": duplicate_rows_removed,
        "total_changes": total_changes,
    }

    return working, summary


def dataframe_to_csv_bytes(
    df: pd.DataFrame,
) -> bytes:
    """Convert a DataFrame to downloadable CSV bytes."""
    return df.to_csv(
        index=False
    ).encode("utf-8")


def dataframe_to_xlsx_bytes(
    df: pd.DataFrame,
) -> bytes:
    """Convert a DataFrame to downloadable XLSX bytes."""
    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Cleaned Data",
        )

    return output.getvalue()