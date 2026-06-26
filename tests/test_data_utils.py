"""pytest unit tests for ``src/data_utils.py``.

Run from the project root with::

    pytest -v
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

# Make ``src`` importable when running pytest from the project root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data_utils import clean_phone, load_csv, validate_email  # noqa: E402


# --------------------------------------------------------------------------- #
# load_csv
# --------------------------------------------------------------------------- #
class TestLoadCsv:
    def test_file_not_found(self):
        """A missing path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_csv("does/not/exist.csv")

    def test_empty_file(self, tmp_path):
        """A zero-byte file raises ValueError."""
        empty = tmp_path / "empty.csv"
        empty.write_text("")
        with pytest.raises(ValueError):
            load_csv(str(empty))

    def test_header_only_file(self, tmp_path):
        """A header with no data rows is also treated as empty."""
        header_only = tmp_path / "header.csv"
        header_only.write_text("a,b,c\n")
        with pytest.raises(ValueError):
            load_csv(str(header_only))

    def test_successful_load(self, tmp_path):
        """A well-formed CSV loads into a DataFrame with the right shape."""
        good = tmp_path / "good.csv"
        good.write_text("customer_id,age\nC001,30\nC002,40\n")
        df = load_csv(str(good))
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)
        assert list(df.columns) == ["customer_id", "age"]


# --------------------------------------------------------------------------- #
# clean_phone
# --------------------------------------------------------------------------- #
class TestCleanPhone:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("4723534498", "472-353-4498"),     # bare 10 digits
            ("423.366.4508", "423-366-4508"),   # dot separated
            ("719-808-4765", "719-808-4765"),   # already hyphenated
            ("(318) 414-9221", "318-414-9221"), # parens + space
            ("733 274 6639", "733-274-6639"),   # space separated
            ("14723534498", "472-353-4498"),    # 11 digits, leading 1
            ("+1 (472) 353-4498", "472-353-4498"),  # intl prefix + symbols
        ],
    )
    def test_valid_formats_normalised(self, raw, expected):
        assert clean_phone(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            "-8437",        # too few digits
            "12345",        # too few digits
            "abcdefghij",   # no digits
            "999999999999", # too many digits
            "",             # empty string
            None,           # missing
            float("nan"),   # NaN from pandas
        ],
    )
    def test_invalid_inputs_return_none(self, raw):
        assert clean_phone(raw) is None

    def test_numeric_input_accepted(self):
        """Integer input (as pandas may supply) is handled."""
        assert clean_phone(4723534498) == "472-353-4498"


# --------------------------------------------------------------------------- #
# validate_email
# --------------------------------------------------------------------------- #
class TestValidateEmail:
    @pytest.mark.parametrize(
        "email",
        [
            "user4875@example.com",
            "first.last@sub.domain.co.uk",
            "name+tag@example.org",
            "  user@example.com  ",  # surrounding whitespace tolerated
        ],
    )
    def test_valid_emails(self, email):
        assert validate_email(email) is True

    @pytest.mark.parametrize(
        "email",
        [
            "@domain.com",          # missing local part
            "invalid-email",        # no @ or domain
            "user@@domain.com",     # double @
            "no-dot@com",           # missing TLD dot
            "user@",                # missing domain
            "missingatsign.com",    # no @
            "user@.com",            # empty domain label
            "user name@domain.com", # space in local part
        ],
    )
    def test_invalid_emails(self, email):
        assert validate_email(email) is False

    @pytest.mark.parametrize("email", [None, float("nan"), 12345, ""])
    def test_edge_cases_non_string_or_missing(self, email):
        assert validate_email(email) is False
