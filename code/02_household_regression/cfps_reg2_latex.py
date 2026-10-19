"""Generate LaTeX tables for CFPS Part 2 Regression 2 (insurance design).

Reads output/reg2/cfps_reg2_column_results.csv and writes:
  - cfps_reg2_main_table.tex
  - cfps_reg2_appendix_A1.tex
  - cfps_reg2_appendix_A2.tex
  - cfps_reg2_appendix_A3.tex
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "outputs" / "tables" / "household"
RESULTS_PATH = OUT_DIR / "cfps_reg2_column_results.csv"

CHILD_TEX = {
    "preschool_age": "PreschoolAge",
    "child_0_15": "ChildAges 0--15",
    "school_age": "SchoolAge",
}


def _stars(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.1:
        return "*"
    return ""


def _coef_cell(coef: float, p: float) -> str:
    return f"{coef:.3f}{_stars(p)}"


def _se_cell(se: float) -> str:
    return f"({se:.3f})"


def _yesno(flag: bool) -> str:
    return "Yes" if flag else "No"


def _strict_sample_label(share) -> str:
    if share is None or (isinstance(share, float) and pd.isna(share)):
        return "All cities"
    pct = int(round(float(share) * 100))
    return f"Top {pct}\\% Strict"


def _controls_label(mode: str) -> str:
    return {
        "none": "No",
        "demo": "Demographics",
        "demo_hukou": "Demo.+hukou",
        "full": "Yes",
    }.get(mode, mode)


def _row_block(label: str, coefs: list[str], ses: list[str]) -> list[str]:
    return [
        label + " & " + " & ".join(coefs) + r" \\",
        " & " + " & ".join(ses) + r" \\",
    ]


def _table_wrapper(
    caption: str,
    label: str,
    tabular_body: str,
    notes: str,
    n_cols: int,
) -> str:
    colspec = "l" + "c" * n_cols
    return "\n".join(
        [
            r"\begin{table}[htbp]",
            r"\centering",
            rf"\caption{{{caption}}}",
            rf"\label{{{label}}}",
            r"\begin{threeparttable}",
            rf"\begin{{tabular}}{{{colspec}}}",
            r"\toprule",
            tabular_body,
            r"\bottomrule",
            r"\end{tabular}",
            r"\begin{tablenotes}[flushleft]",
            r"\footnotesize",
            notes,
            r"\end{tablenotes}",
            r"\end{threeparttable}",
            r"\end{table}",
            "",
        ]
    )


def build_main_table(df: pd.DataFrame) -> str:
    cols = [df.loc[df["col_id"] == c].iloc[0] for c in ["1", "2", "3", "4", "5"]]
    headers = " & ".join(f"({c.col_id})" for c in cols)
    sample_hdr = " & ".join(c.label for c in cols)

    body_lines = [
        f" & {headers} \\\\",
        f" & {sample_hdr} \\\\",
        r"\midrule",
        r"\multicolumn{6}{l}{\textit{Dependent variable:} OwnHouse} \\",
        r"\midrule",
    ]

    # Coefficient rows
    body_lines += _row_block(
        r"Migrant ($M$)",
        [_coef_cell(c.m_coef, c.m_p) for c in cols],
        [_se_cell(c.m_se) for c in cols],
    )
    # Child main effect: label depends on column child definition
    # Use a generic "Child" row; footnote clarifies definitions by column
    body_lines += _row_block(
        r"Child",
        [_coef_cell(c.child_coef, c.child_p) for c in cols],
        [_se_cell(c.child_se) for c in cols],
    )
    body_lines += _row_block(
        r"$M \times$ Child",
        [_coef_cell(c.mxp_coef, c.mxp_p) for c in cols],
        [_se_cell(c.mxp_se) for c in cols],
    )

    body_lines += [
        r"\midrule",
        "Child definition & "
        + " & ".join(CHILD_TEX[c.child_var] for c in cols)
        + r" \\",
        "Strict sample & "
        + " & ".join(_strict_sample_label(c.strict_share) for c in cols)
        + r" \\",
        "Age window & "
        + " & ".join(["25--50"] * len(cols))
        + r" \\",
        "City FE & "
        + " & ".join(["Yes"] * len(cols))
        + r" \\",
        "Year FE & "
        + " & ".join(["Yes"] * len(cols))
        + r" \\",
        "Controls & "
        + " & ".join([_controls_label(c.controls) for c in cols])
        + r" \\",
        "Observations & "
        + " & ".join(f"{int(c.nobs):,}" for c in cols)
        + r" \\",
        "Cities & "
        + " & ".join(str(int(c.n_cities)) for c in cols)
        + r" \\",
        r"$M \times$ Child cell $N$ & "
        + " & ".join(str(int(c.n_mxp_cell)) for c in cols)
        + r" \\",
    ]

    notes = r"""
\item \textit{Notes:} Linear probability models. The sample is urban CFPS households in 2014, 2016, and 2018 whose financial respondent is aged 25--50. \textit{OwnHouse} equals one if the household owns (full or partial) title to the current dwelling. \textit{Migrant} equals one if the respondent's hukou is outside the current county/city. Column (1) uses all matched cities; columns (2)--(5) retain cities in the top share of the Part~1 composite restriction index $\mathrm{Strict}=h(1+h_2)$. Child equals PreschoolAge (ages 0--5) in columns (1)--(3), ages 0--15 in column (4), and SchoolAge (6--15) in column (5). Controls include age, gender, years of schooling, marital status, hukou type, household size, and log per-capita income. City-clustered standard errors in parentheses. $^{*}p<0.10$, $^{**}p<0.05$, $^{***}p<0.01$. Column (3) is the preferred specification.
""".strip()

    return _table_wrapper(
        caption="Household Homeownership and Intergenerational Insurance: CFPS Mechanism Estimates",
        label="tab:cfps_reg2_main",
        tabular_body="\n".join(body_lines),
        notes=notes,
        n_cols=5,
    )


def build_appendix_table(
    df: pd.DataFrame,
    col_ids: list[str],
    caption: str,
    label: str,
    notes: str,
    header_mode: str = "label",
) -> str:
    cols = [df.loc[df["col_id"] == c].iloc[0] for c in col_ids]
    n = len(cols)
    headers = " & ".join(f"({i + 1})" for i in range(n))
    if header_mode == "label":
        sub = " & ".join(c.label for c in cols)
    else:
        sub = " & ".join(_strict_sample_label(c.strict_share) for c in cols)

    body = [
        f" & {headers} \\\\",
        f" & {sub} \\\\",
        r"\midrule",
        rf"\multicolumn{{{n + 1}}}{{l}}{{\textit{{Dependent variable:}} OwnHouse}} \\",
        r"\midrule",
    ]
    body += _row_block(
        r"Migrant ($M$)",
        [_coef_cell(c.m_coef, c.m_p) for c in cols],
        [_se_cell(c.m_se) for c in cols],
    )
    body += _row_block(
        r"PreschoolAge ($P$)",
        [_coef_cell(c.child_coef, c.child_p) for c in cols],
        [_se_cell(c.child_se) for c in cols],
    )
    body += _row_block(
        r"$M \times P$",
        [_coef_cell(c.mxp_coef, c.mxp_p) for c in cols],
        [_se_cell(c.mxp_se) for c in cols],
    )
    body += [
        r"\midrule",
        "Controls & " + " & ".join(_controls_label(c.controls) for c in cols) + r" \\",
        "Drop Shanghai & "
        + " & ".join(_yesno(bool(c.drop_shanghai)) for c in cols)
        + r" \\",
        "City FE / Year FE & " + " & ".join(["Yes"] * n) + r" \\",
        "Observations & " + " & ".join(f"{int(c.nobs):,}" for c in cols) + r" \\",
        "Cities & " + " & ".join(str(int(c.n_cities)) for c in cols) + r" \\",
        r"$M \times P$ cell $N$ & "
        + " & ".join(str(int(c.n_mxp_cell)) for c in cols)
        + r" \\",
    ]
    return _table_wrapper(caption, label, "\n".join(body), notes, n)


def main() -> None:
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Missing {RESULTS_PATH}. Run: python src/regressions/cfps_reg2_insurance.py"
        )
    df = pd.read_csv(RESULTS_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    main_tex = build_main_table(df)
    (OUT_DIR / "cfps_reg2_main_table.tex").write_text(main_tex, encoding="utf-8")

    a1 = build_appendix_table(
        df,
        ["A1a", "A1b", "A1c", "A1d"],
        caption="Robustness: Stepwise Controls (Top 60\\% Strict, PreschoolAge)",
        label="tab:cfps_reg2_A1",
        notes=r"""
\item \textit{Notes:} Same sample as column (3) of Table~\ref{tab:cfps_reg2_main}. Column (1) includes only city and year fixed effects. Column (2) adds age, gender, schooling, and marital status. Column (3) further adds hukou type. Column (4) adds household size and log per-capita income. City-clustered standard errors in parentheses. $^{*}p<0.10$, $^{**}p<0.05$, $^{***}p<0.01$.
""".strip(),
    )
    (OUT_DIR / "cfps_reg2_appendix_A1.tex").write_text(a1, encoding="utf-8")

    a2 = build_appendix_table(
        df,
        ["A2a", "A2b", "A2c", "A2d"],
        caption="Robustness: Alternative High-Strict Thresholds",
        label="tab:cfps_reg2_A2",
        notes=r"""
\item \textit{Notes:} All columns use PreschoolAge, the age 25--50 window, full controls, and city/year fixed effects. Cities are ranked by mean $\mathrm{Strict}=h(1+h_2)$. City-clustered standard errors in parentheses. $^{*}p<0.10$, $^{**}p<0.05$, $^{***}p<0.01$.
""".strip(),
        header_mode="strict",
    )
    (OUT_DIR / "cfps_reg2_appendix_A2.tex").write_text(a2, encoding="utf-8")

    a3 = build_appendix_table(
        df,
        ["A3a", "A3b", "A3c"],
        caption="Robustness: Excluding Shanghai",
        label="tab:cfps_reg2_A3",
        notes=r"""
\item \textit{Notes:} Column (1) repeats the preferred Top 60\\% Strict specification. Columns (2)--(3) drop Shanghai households. The attenuation after excluding Shanghai indicates that the differential is concentrated in the highest-restriction megacities represented in CFPS. City-clustered standard errors in parentheses. $^{*}p<0.10$, $^{**}p<0.05$, $^{***}p<0.01$.
""".strip(),
    )
    (OUT_DIR / "cfps_reg2_appendix_A3.tex").write_text(a3, encoding="utf-8")

    # Combined file for easy \input
    mech_app = OUT_DIR / "cfps_reg2_mechanism_appendix.tex"
    parts = [
        "% Auto-generated CFPS Regression 2 tables. Requires booktabs, threeparttable.",
        main_tex,
        a1,
        a2,
        a3,
    ]
    if mech_app.exists():
        parts.append(mech_app.read_text(encoding="utf-8"))
    (OUT_DIR / "cfps_reg2_tables.tex").write_text("\n".join(parts), encoding="utf-8")

    print(f"Wrote {OUT_DIR / 'cfps_reg2_main_table.tex'}")
    print(f"Wrote {OUT_DIR / 'cfps_reg2_appendix_A1.tex'}")
    print(f"Wrote {OUT_DIR / 'cfps_reg2_appendix_A2.tex'}")
    print(f"Wrote {OUT_DIR / 'cfps_reg2_appendix_A3.tex'}")
    if mech_app.exists():
        print(f"Wrote {mech_app} (included in combined)")
    print(f"Wrote {OUT_DIR / 'cfps_reg2_tables.tex'}")


if __name__ == "__main__":
    main()
