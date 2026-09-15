# Build tools

`paper/index.html` and the release PDFs are generated from the Markdown; do not edit them by hand.

```bash
# 1. Markdown -> HTML bodies (pandoc 3.x)
pandoc paper/README.md -f gfm -t html5 -o tools/paper-body.html
pandoc paper/methodology.md -f gfm -t html5 -o tools/appendix-body.html
# 2. the web edition: paper + Appendix A, sidebar, canvas charts
python3 tools/build_html.py            # writes paper/index.html
# 3. draft PDFs for proofing (headless Chrome); the released PDF under releases/ is the designed edition, not this output
python3 tools/build_print.py           # writes tools/out/*.pdf
# 4. vector figures and Word editions (inputs to the designed release)
python3 tools/build_svg.py             # writes paper/figures/svg/*.svg
python3 tools/build_docx.py            # writes tools/out/*.docx
```

`site.css` and `charts.js` are inlined into the web edition; `print.css` styles the PDFs. Chart data lives in `build_html.py` and is copied from the paper's tables.
