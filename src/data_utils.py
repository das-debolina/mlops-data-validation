"""Data utility functions for the customer-data validation pipeline.

These three helpers are the units exercised by the pytest suite in
``tests/test_data_utils.py``:

* ``load_csv``      – defensive CSV loading.
* ``clean_phone``   – normalise the many phone-number formats in the dataset.
* ``validate_email`` – check an address against a pragmatic email regex.
"""

from __future__ import annotations

import os
import re

import pandas as pd

# A pragmatic email pattern: one local part, one "@", a dotted domain, and a
# TLD of at least two letters. It deliberately rejects the malformed addresses
# seen in the dataset (``@domain.com``, ``user@``, ``no-dot@com`` ...).
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")


def load_csv(filepath: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame with defensive checks.

    Parameters
    ----------
    filepath:
        Path to the CSV file.

    Returns
    -------
    pandas.DataFrame
        The parsed contents of the file.

    Raises
    ------
    FileNotFoundError
        If ``filepath`` does not point at an existing file.
    ValueError
        If the file exists but contains no rows (an empty dataset).
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"No such file: {filepath}")

    try:
        df = pd.read_csv(filepath)
    except pd.errors.EmptyDataError as exc:  # zero bytes / no header
        raise ValueError(f"File is empty: {filepath}") from exc

    if df.empty:
        raise ValueError(f"File contains no rows: {filepath}")

    return df


def clean_phone(phone) -> str | None:
    """Normalise a phone number to a canonical ``XXX-XXX-XXXX`` string.

    The dataset stores numbers in many shapes – ``4723534498``,
    ``423.366.4508``, ``(318) 414-9221``, ``733 274 6639`` and junk values such
    as ``-8437``. This function strips every non-digit character and, when
    exactly ten digits remain, reformats them as ``XXX-XXX-XXXX``. Eleven-digit
    numbers with a leading ``1`` country code are accepted and the ``1`` is
    dropped.

    Parameters
    ----------
    phone:
        The raw phone value (string, number, or NaN/None).

    Returns
    -------
    str or None
        The cleaned ``XXX-XXX-XXXX`` string, or ``None`` when the input cannot
        yield a valid 10-digit number.
    """
    if phone is None:
        return None
    # Treat pandas/NumPy NaN as missing.
    if isinstance(phone, float) and pd.isna(phone):
        return None

    digits = re.sub(r"\D", "", str(phone))

    # Drop a leading "1" country code on 11-digit numbers.
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]

    if len(digits) != 10:
        return None

    return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"


def validate_email(email) -> bool:
    """Return ``True`` when ``email`` is a syntactically valid address.

    Parameters
    ----------
    email:
        The value to test. Non-string or missing values return ``False``.

    Returns
    -------
    bool
        Whether the value matches :data:`EMAIL_REGEX`.
    """
    if not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))
