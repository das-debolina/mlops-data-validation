"""Render report screenshots from the real validation + pytest output.

Produces two PNGs under ``report_assets/``:
  * gx_validation_results.png – a self-contained summary of the suite run.
  * pytest_results.png        – a terminal-style capture of ``pytest -v``.

These are convenience artefacts for the markdown report. The authentic
Great Expectations Data Docs site still lives under
``gx/uncommitted/data_docs/local_site/`` and renders with full styling in a
browser with internet access.
"""

from __future__ import annotations

import html
import os
import subprocess

import great_expectations as gx
import great_expectations.expectations as gxe

import great_expectations_setup as setup  # reuse build_suite + constants

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "report_assets")
os.makedirs(ASSETS, exist_ok=True)


def run_validation():
    import pandas as pd
    context = gx.get_context(mode="file", project_root_dir=ROOT)
    df = pd.read_csv(os.path.join(ROOT, "data", "customer_data.csv"))
    ds = context.data_sources.get("customer_data_source")
    asset = ds.get_asset("customer_data_asset")
    bd = asset.get_batch_definition("all_customer_data")
    suite = setup.build_suite(context)
    try:
        context.validation_definitions.delete(name="report_run")
    except Exception:
        pass
    vd = context.validation_definitions.add(
        gx.ValidationDefinition(data=bd, suite=suite, name="report_run")
    )
    return vd.run(batch_parameters={"dataframe": df})


LABELS = {
    "expect_column_values_to_be_unique": "Values are unique",
    "expect_column_values_to_not_be_null": "Values are not null",
    "expect_column_values_to_be_between": "Values between 0 and 120",
    "expect_column_values_to_match_regex": "Values match email format",
    "expect_column_values_to_be_in_set": "Values in {USA, Canada, UK, Australia}",
    "expect_column_values_to_be_of_type": "Values are datetime type",
    "expect_table_row_count_to_be_between": "Row count between 500 and 1000",
}


def build_html(results) -> str:
    total = len(results.results)
    passed = sum(1 for r in results.results if r.success)
    rows = []
    for r in results.results:
        cfg = r.expectation_config
        col = cfg.kwargs.get("column", "(table)")
        label = LABELS.get(cfg.type, cfg.type)
        ok = r.success
        unexpected = r.result.get("unexpected_count")
        observed = r.result.get("observed_value")
        if unexpected is not None:
            detail = f"{unexpected:,} unexpected of {r.result.get('element_count'):,}"
        elif observed is not None:
            detail = f"observed: {html.escape(str(observed))}"
        else:
            detail = ""
        badge = "PASS" if ok else "FAIL"
        cls = "pass" if ok else "fail"
        rows.append(
            f"<tr class='{cls}'>"
            f"<td class='status'><span class='badge {cls}'>{badge}</span></td>"
            f"<td class='col'>{html.escape(col)}</td>"
            f"<td>{html.escape(label)}</td>"
            f"<td class='detail'>{detail}</td></tr>"
        )
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 28px; background: #f7f8fa; color: #1c2430; }}
    .card {{ max-width: 980px; background: #fff; border: 1px solid #e3e7ee;
             border-radius: 12px; overflow: hidden; }}
    .head {{ padding: 20px 26px; border-bottom: 1px solid #eef1f5; }}
    h1 {{ font-size: 19px; margin: 0 0 4px; }}
    .sub {{ color: #6b7480; font-size: 13px; }}
    .summary {{ display: flex; gap: 10px; padding: 16px 26px;
                border-bottom: 1px solid #eef1f5; }}
    .pill {{ font-size: 13px; padding: 6px 12px; border-radius: 999px; font-weight: 600; }}
    .pill.fail {{ background: #fdecec; color: #b3261e; }}
    .pill.muted {{ background: #eef1f5; color: #46505c; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 11px 26px; font-size: 13px;
              border-bottom: 1px solid #f0f2f6; }}
    th {{ font-size: 11px; letter-spacing: .06em; text-transform: uppercase;
          color: #8a929d; }}
    .col {{ font-family: 'SF Mono', Menlo, monospace; color: #2a3340; }}
    .detail {{ color: #6b7480; }}
    .badge {{ font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 5px; }}
    .badge.pass {{ background: #e6f4ea; color: #1e7e34; }}
    .badge.fail {{ background: #fdecec; color: #b3261e; }}
    tr.fail .col {{ color: #b3261e; }}
    </style></head><body>
    <div class='card'>
      <div class='head'>
        <h1>Expectation Validation Result &mdash; customer_data_expectations</h1>
        <div class='sub'>Data asset: customer_data.csv &nbsp;&bull;&nbsp; 5,015 rows evaluated</div>
      </div>
      <div class='summary'>
        <span class='pill fail'>Overall: Failed</span>
        <span class='pill muted'>{passed} of {total} expectations passed</span>
      </div>
      <table>
        <thead><tr><th>Status</th><th>Column</th><th>Expectation</th><th>Result</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div></body></html>"""


def render(html_path, png_path, width=1040):
    subprocess.run(
        ["wkhtmltoimage", "--quiet", "--enable-local-file-access",
         "--width", str(width), html_path, png_path],
        check=False,
    )


def main():
    results = run_validation()
    html_path = os.path.join(ASSETS, "gx_validation_results.html")
    with open(html_path, "w") as fh:
        fh.write(build_html(results))
    render(html_path, os.path.join(ASSETS, "gx_validation_results.png"))

    # pytest terminal capture
    proc = subprocess.run(
        ["python3", "-m", "pytest", "-v", "--no-header"],
        cwd=ROOT, capture_output=True, text=True,
    )
    out = proc.stdout
    term_html = (
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        "body{margin:0;padding:0;background:#0d1117;}"
        ".term{font-family:'SF Mono',Menlo,Consolas,monospace;font-size:12.5px;"
        "line-height:1.55;color:#c9d1d9;background:#0d1117;padding:20px 24px;"
        "white-space:pre-wrap;}"
        ".pass{color:#3fb950;}.fail{color:#f85149;}.dim{color:#8b949e;}"
        "</style></head><body><div class='term'>"
    )
    for line in out.splitlines():
        safe = html.escape(line)
        if "PASSED" in line:
            safe = safe.replace("PASSED", "<span class='pass'>PASSED</span>")
        if "passed" in line and "=" in line:
            safe = f"<span class='pass'>{safe}</span>"
        if "FAILED" in line or "error" in line.lower():
            safe = f"<span class='fail'>{safe}</span>"
        term_html += safe + "\n"
    term_html += "</div></body></html>"
    tpath = os.path.join(ASSETS, "pytest_results.html")
    with open(tpath, "w") as fh:
        fh.write(term_html)
    render(tpath, os.path.join(ASSETS, "pytest_results.png"), width=920)
    print("Rendered report assets to", ASSETS)


if __name__ == "__main__":
    main()
