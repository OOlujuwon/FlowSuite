from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.services.cleanflow import (
    SUPPORTED_EXTENSIONS,
    clean_dataframe,
    dataframe_to_csv_bytes,
    dataframe_to_xlsx_bytes,
    load_dataframe,
)


router = APIRouter(
    prefix="/cleanflow",
    tags=["CleanFlow"],
)

templates = Jinja2Templates(
    directory="templates"
)


# Temporary in-memory storage for the current browser session.
# This keeps the MVP simple and avoids creating user accounts.
cleaning_jobs: dict[str, dict] = {}


MAX_FILE_SIZE = 25 * 1024 * 1024


@router.get(
    "/",
    response_class=HTMLResponse,
)
def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="cleanflow/dashboard.html",
        context={
            "supported_extensions": sorted(
                extension.upper()
                for extension in SUPPORTED_EXTENSIONS
            ),
        },
    )


@router.post(
    "/clean",
    response_class=HTMLResponse,
)
async def clean_file(
    request: Request,
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please select a file.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Please upload a CSV or XLSX file."
            ),
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File is too large. Maximum size is 25 MB.",
        )

    try:
        dataframe = load_dataframe(
            filename=file.filename,
            file_bytes=file_bytes,
        )

        cleaned_dataframe, summary = clean_dataframe(
            dataframe
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not process file: {exc}",
        )

    job_id = uuid4().hex

    cleaning_jobs[job_id] = {
        "original_filename": file.filename,
        "extension": extension,
        "dataframe": cleaned_dataframe,
        "summary": summary,
    }

    preview = cleaned_dataframe.head(10).fillna("").to_dict(
        orient="records"
    )

    return templates.TemplateResponse(
        request=request,
        name="cleanflow/result.html",
        context={
            "job_id": job_id,
            "filename": file.filename,
            "summary": summary,
            "columns": list(cleaned_dataframe.columns),
            "preview": preview,
        },
    )


@router.get(
    "/download/{job_id}/{format}",
)
def download_cleaned_file(
    job_id: str,
    format: str,
):
    job = cleaning_jobs.get(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Cleaning job not found.",
        )

    dataframe = job["dataframe"]
    original_filename = job["original_filename"]

    stem = Path(original_filename).stem

    if format == "csv":
        content = dataframe_to_csv_bytes(dataframe)

        filename = f"{stem}_cleaned.csv"

        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename}"'
                )
            },
        )

    if format == "xlsx":
        content = dataframe_to_xlsx_bytes(dataframe)

        filename = f"{stem}_cleaned.xlsx"

        return Response(
            content=content,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename}"'
                )
            },
        )

    raise HTTPException(
        status_code=400,
        detail="Download format must be CSV or XLSX.",
    )