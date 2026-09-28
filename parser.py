import pandas as pd
import os


def load_statement(filepath):
    """
    Handles both .xlsx and .csv M-Pesa exports.
    Both formats can have the same pagination problem: repeated
    'Receipt No.' header rows interspersed with disclaimer/summary text.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".xlsx":
        raw_tables = _read_xlsx_raw(filepath)
    elif ext == ".csv":
        raw_tables = _read_csv_raw(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Please upload a .csv or .xlsx file.")

    transaction_frames = _extract_transaction_chunks(raw_tables)

    if not transaction_frames:
        raise ValueError("No transaction tables found in this file.")

    combined = pd.concat(transaction_frames, ignore_index=True)
    return normalize_transactions(combined)


def _read_xlsx_raw(filepath):
    """Returns a list of raw (header=None) DataFrames, one per sheet."""
    xl = pd.ExcelFile(filepath)
    return [xl.parse(sheet_name, header=None) for sheet_name in xl.sheet_names]


def _read_csv_raw(filepath):
    """
    Returns a list containing one raw DataFrame — the whole CSV read with
    no header assumed, since we don't yet know where the real header row is.
    """
    raw = pd.read_csv(filepath, header=None)
    return [raw]


def _extract_transaction_chunks(raw_tables):
    """
    Shared chunk-finder: works on a list of raw tables (sheets, or a single
    flat CSV table). Scans for rows containing 'Receipt No' to find each
    header, then captures rows below it as one chunk until the next header
    row or the end of the table.
    """
    transaction_frames = []

    for raw in raw_tables:
        if raw.shape[0] < 2:
            continue

        # Find every row index that looks like a header row
        header_row_indices = []
        for idx, row in raw.iterrows():
            row_text = " ".join(str(x) for x in row.tolist())
            if "Receipt No" in row_text:
                header_row_indices.append(idx)

        if not header_row_indices:
            continue

        # Slice out each chunk: from one header row to just before the next one
        for i, header_idx in enumerate(header_row_indices):
            start = header_idx
            end = header_row_indices[i + 1] if i + 1 < len(header_row_indices) else raw.shape[0]

            chunk = raw.iloc[start:end].reset_index(drop=True)
            chunk.columns = chunk.iloc[0]
            data = chunk[1:].reset_index(drop=True)

            # Drop fully-blank columns (handles the 7-vs-8 column inconsistency)
            data = data.dropna(axis=1, how="all")

            # Drop any trailing disclaimer/footer rows that snuck in
            # (a real row should have a non-empty Receipt No value)
            if "Receipt No." in data.columns:
                data = data[data["Receipt No."].notna()]

            if not data.empty:
                transaction_frames.append(data)

    return transaction_frames


def normalize_transactions(df):
    """Turns the raw parsed columns into a clean, consistent structure."""
    df = df.rename(columns={
        "Receipt No.": "receipt_no",
        "Completion Time": "completion_time",
        "Details": "details",
        "Transaction Status": "status",
        "Paid In": "paid_in",
        "Withdrawn": "withdrawn",
        "Balance": "balance",
    })

    # Keep only completed transactions
    df = df[df["status"] == "Completed"].copy()

    # Collapse Paid In / Withdrawn into one signed amount column
    df["paid_in"] = pd.to_numeric(df["paid_in"], errors="coerce").fillna(0)
    df["withdrawn"] = pd.to_numeric(df["withdrawn"], errors="coerce").fillna(0)
    df["amount"] = df["paid_in"] + df["withdrawn"]  # withdrawn is already negative

    df["completion_time"] = pd.to_datetime(df["completion_time"], errors="coerce")
    df["balance"] = pd.to_numeric(df["balance"], errors="coerce")

    return df[["receipt_no", "completion_time", "details", "amount", "balance"]]


def load_sales_record(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(filepath)
    elif ext == ".xlsx":
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Please upload a .csv or .xlsx file.")

    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={"date": "sale_date", "description": "description", "amount": "amount"})

    required_cols = {"sale_date", "amount"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Sales file is missing required columns: {required_cols - set(df.columns)}")

    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df[["sale_date", "description", "amount"]]