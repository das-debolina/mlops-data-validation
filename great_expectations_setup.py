"""Great Expectations setup, suite definition, validation, and Data Docs.

This single script covers Parts 1-3 of the assignment using the
Great Expectations 1.x fluent API:

* initialises a file-backed GX project (``gx/`` folder),
* registers a pandas filesystem data source pointing at ``data/``,
* builds the ``customer_data_expectations`` suite (8 expectations),
* validates the messy CSV and prints a per-issue summary,
* builds the HTML Data Docs site.

Run from the project root::

    python great_expectations_setup.py
"""

from __future__ import annotations

import os

import great_expectations as gx
import great_expectations.expectations as gxe

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SUITE_NAME = "customer_data_expectations"

# Same pattern used by ``validate_email`` in src/data_utils.py.
EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"


def build_suite(context) -> gx.ExpectationSuite:
    """Create (or replace) the expectation suite with all eight expectations."""
    # Start clean so re-runs don't raise "already exists".
    try:
        context.suites.delete(name=SUITE_NAME)
    except Exception:
        pass

    suite = context.suites.add(gx.ExpectationSuite(name=SUITE_NAME))

    # 1 & 2. customer_id must be unique and not null.
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="customer_id"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="customer_id"))

    # 3. age between 0 and 120.
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="age", min_value=0, max_value=120)
    )

    # 4. email must match a valid format.
    suite.add_expectation(
        gxe.ExpectColumnValuesToMatchRegex(column="email", regex=EMAIL_REGEX)
    )

    # 5. salary present in at least 95% of rows (mostly parameter).
    suite.add_expectation(
        gxe.ExpectColumnValuesToNotBeNull(column="salary", mostly=0.95)
    )

    # 6. country in the allowed set.
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeInSet(
            column="country", value_set=["USA", "Canada", "UK", "Australia"]
        )
    )

    # 7. signup_date must be of datetime type. Read straight from CSV the
    #    column arrives as an object/string, so this expectation legitimately
    #    flags that the dates were never parsed into a datetime dtype.
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeOfType(
            column="signup_date", type_="datetime64[ns]"
        )
    )

    # 8. overall row count between 500 and 1000.
    suite.add_expectation(
        gxe.ExpectTableRowCountToBeBetween(min_value=500, max_value=1000)
    )

    return suite


def main() -> None:
    import pandas as pd

    # Part 1: file-backed project + pandas DataFrame data source.
    # We load the CSV with pandas and hand GX the DataFrame directly. This is
    # more robust than a filesystem data source: it avoids path-matching issues
    # (including project paths that contain spaces) across GX point releases.
    context = gx.get_context(mode="file", project_root_dir=PROJECT_ROOT)

    csv_path = os.path.join(DATA_DIR, "customer_data.csv")
    df = pd.read_csv(csv_path)

    source_name = "customer_data_source"
    try:
        data_source = context.data_sources.get(source_name)
    except (KeyError, ValueError):
        data_source = context.data_sources.add_pandas(name=source_name)

    asset_name = "customer_data_asset"
    try:
        asset = data_source.get_asset(asset_name)
    except (LookupError, ValueError):
        asset = data_source.add_dataframe_asset(name=asset_name)

    batch_name = "all_customer_data"
    try:
        batch_def = asset.get_batch_definition(batch_name)
    except (KeyError, ValueError):
        batch_def = asset.add_batch_definition_whole_dataframe(batch_name)

    # Part 2: build the suite.
    suite = build_suite(context)

    # Part 3: validate. The DataFrame is supplied at run time via
    # batch_parameters (DataFrame assets are not serialised into the project).
    validation_name = "customer_data_validation"
    try:
        context.validation_definitions.delete(name=validation_name)
    except Exception:
        pass
    validation_definition = context.validation_definitions.add(
        gx.ValidationDefinition(
            data=batch_def, suite=suite, name=validation_name
        )
    )

    results = validation_definition.run(batch_parameters={"dataframe": df})

    # Console summary of each expectation result.
    print("\n" + "=" * 78)
    print(f"VALIDATION SUMMARY  –  success: {results.success}")
    print("=" * 78)
    for r in results.results:
        cfg = r.expectation_config
        col = cfg.kwargs.get("column", "TABLE")
        flag = "PASS" if r.success else "FAIL"
        unexpected = r.result.get("unexpected_count")
        element = r.result.get("element_count")
        extra = ""
        if unexpected is not None:
            extra = f"  unexpected={unexpected}/{element}"
        elif "observed_value" in r.result:
            extra = f"  observed={r.result['observed_value']}"
        print(f"  [{flag}] {cfg.type:42s} {col:14s}{extra}")

    # Part 3: build HTML Data Docs.
    context.build_data_docs()
    docs_index = os.path.join(
        PROJECT_ROOT, "gx", "uncommitted", "data_docs", "local_site", "index.html"
    )
    print("\nData Docs built at:", docs_index)


if __name__ == "__main__":
    main()
