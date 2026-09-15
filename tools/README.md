# Build tools

`paper/index.html` and the release PDFs are generated from the Markdown; do not edit them by hand.

```bash
# 1. Markdown -> HTML bodies (pandoc 3.x)
pandoc paper/README.md -f gfm -t html5 -o tools/paper-body.html
pandoc paper/methodology.md -f gfm -t html5 -o tools/appendix-body.html
# 2. the web edition: paper + Appendix A, sidebar, canvas charts
python3 tools/build_html.py            # writes paper/index.html
# 3. the release PDFs: A4, running heads, page numbers (headless Chrome)
python3 tools/build_print.py           # writes releases/acropolis-v1.0.pdf and -appendix-a.pdf
```

`site.css` and `charts.js` are inlined into the web edition; `print.css` styles the PDFs. Chart data lives in `build_html.py` and is copied from the paper's tables.
