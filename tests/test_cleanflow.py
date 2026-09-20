from io import BytesIO

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.services.cleanflow import (
    clean_dataframe,
    dataframe_to_csv_bytes,
    dataframe_to_xlsx_bytes,
    load_dataframe,
)


client = TestClient(app)


def test_clean_dataframe_removes_duplicates_and_empty_rows():
    dataframe = pd.DataFrame(
        {
            " Customer Name ": [
                " Ada ",
                "Ada",
                " Tunde ",
                None,
            ],
            "Email Address": [
                "ada@example.com",
                "ada@example.com",
                "tunde@example.com",
                None,
            ],
        }
    )

    cleaned, summary = clean_dataframe(dataframe)

    assert len(cleaned) == 2
    assert summary["duplicate_rows_removed"] == 1
    assert summary["empty_rows_removed"] == 1


def test_column_names_are_normalized():
    dataframe = pd.DataFrame(
        {
            " First Name ": ["Ada"],
            "Email-Address": ["ada@example.com"],
            "Phone Number": ["08000000000"],
        }
    )

    cleaned, summary = clean_dataframe(dataframe)

    assert list(cleaned.columns) == [
        "first_name",
        "email_address",
        "phone_number",
    ]

    assert summary["columns_renamed"] == 3


def test_blank_strings_are_cleaned_and_empty_rows_removed():
    dataframe = pd.DataFrame(
        {
            "Name": ["Ada", "   ", "Tunde"],
        }
    )

    cleaned, summary = clean_dataframe(dataframe)

    assert summary["whitespace_cells_cleaned"] == 1
    assert summary["empty_rows_removed"] == 1
    assert list(cleaned["name"]) == ["Ada", "Tunde"]


def test_csv_loading():
    csv_content = (
        "Name,Email\n"
        "Ada,ada@example.com\n"
    ).encode("utf-8")

    dataframe = load_dataframe(
        "customers.csv",
        csv_content,
    )

    assert list(dataframe.columns) == [
        "Name",
        "Email",
    ]

    assert len(dataframe) == 1


def test_xlsx_loading():
    original = pd.DataFrame(
        {
            "Name": ["Ada"],
            "Email": ["ada@example.com"],
        }
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        original.to_excel(
            writer,
            index=False,
        )

    dataframe = load_dataframe(
        "customers.xlsx",
        output.getvalue(),
    )

    assert list(dataframe.columns) == [
        "Name",
        "Email",
    ]

    assert len(dataframe) == 1


def test_csv_export():
    dataframe = pd.DataFrame(
        {
            "name": ["Ada"],
            "email": ["ada@example.com"],
        }
    )

    output = dataframe_to_csv_bytes(dataframe)

    assert b"name,email" in output
    assert b"Ada,ada@example.com" in output


def test_xlsx_export():
    dataframe = pd.DataFrame(
        {
            "name": ["Ada"],
            "email": ["ada@example.com"],
        }
    )

    output = dataframe_to_xlsx_bytes(dataframe)

    assert output[:2] == b"PK"


def test_cleanflow_page():
    response = client.get("/cleanflow/")

    assert response.status_code == 200
    assert "CleanFlow" in response.text
    assert "Clean my file" in response.text


def test_cleanflow_upload_and_download():
    csv_content = (
        " Customer Name ,Email Address\n"
        " Ada ,ada@example.com\n"
        " Ada ,ada@example.com\n"
        " Tunde ,tunde@example.com\n"
    ).encode("utf-8")

    response = client.post(
        "/cleanflow/clean",
        files={
            "file": (
                "customers.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    assert "Cleaning complete" in response.text
    assert "duplicate" in response.text.lower()

    # Extract the generated job ID from the response.
    marker = "/cleanflow/download/"
    start = response.text.index(marker) + len(marker)
    end = response.text.index(
        "/csv",
        start,
    )

    job_id = response.text[start:end]

    download = client.get(
        f"/cleanflow/download/{job_id}/csv"
    )

    assert download.status_code == 200
    assert "first_name" in download.text or "customer_name" in download.text
    assert "ada@example.com" in download.text


def test_unsupported_file_type_is_rejected():
    response = client.post(
        "/cleanflow/clean",
        files={
            "file": (
                "customers.txt",
                b"hello",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400