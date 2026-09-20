# FlowSuite

FlowSuite is a lightweight business operations suite built with Python and FastAPI.

## Tools

- **ClientFlow** — customer records, CRM and follow-ups
- **PayFlow** — invoices, payments and balances
- **CleanFlow** — CSV/XLSX data cleaning and export
- **Automation** — repeatable business operations

## Technology

- Python
- FastAPI
- SQLModel
- SQLite
- Jinja2
- Bootstrap
- Pandas
- openpyxl
- Pytest

## Current MVP

FlowSuite currently provides customer management, CRM and follow-ups through ClientFlow; invoice, payment and balance management through PayFlow; CSV/XLSX cleaning and export through CleanFlow; and manual and scheduled automation.

## Product Model

FlowSuite is designed around simple, outcome-focused business tools. The intended model is pay-per-use rather than requiring customers to maintain a complicated software account.

## Commercialisation

The next commercialisation layer will add payment-gateway processing, payment verification, customer-facing purchase flows, persistent storage, transaction records and production file handling.

## Development

Run the application with:

    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Run tests with:

    .\.venv\Scripts\python.exe -m pytest -q

## Status

**MVP — core functionality complete.**

