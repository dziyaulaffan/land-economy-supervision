"""Build outputs/supervision/supervision.tex from scripts/supervision_template.tex and the estimation outputs.

The supervision summary reuses the chart builders of 99_report.py, so every plotted coefficient comes from the same
CSV outputs as the full report. The tables in the template are static and their figures are taken from
ESTIMATION_NOTES.md, extension/EXTENSION_NOTES.md, extension/venue_mix/VENUE_MIX_NOTES.md and
extension/recovery/RECOVERY_NOTES.md. The result is a single self-contained .tex file for Overleaf (pdflatex).
"""
import importlib.util
import re
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("report", HERE / "99_report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)

OUTDIR = HERE.parent / "outputs" / "supervision"


def main():
    tpl = (HERE / "supervision_template.tex").read_text(encoding="utf-8")
    frags = report.build()
    keys = set(re.findall(r"<<([A-Z0-9_]+)>>", tpl))
    missing = keys - set(frags)
    assert not missing, f"template placeholders without data: {missing}"
    for k in keys:
        tpl = tpl.replace(f"<<{k}>>", frags[k])
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "supervision.tex"
    out.write_text(tpl, encoding="utf-8")
    print("written", out)


if __name__ == "__main__":
    main()
