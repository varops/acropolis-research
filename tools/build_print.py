import re, subprocess, sys
import os; S=os.path.dirname(os.path.abspath(__file__))
R=os.path.dirname(S)
page=open(f"{R}/paper/index.html").read()
css=open(f"{S}/print.css").read()
main=re.search(r'<main class="doc" id="top">(.*?)</main>', page, re.S).group(1)
scripts=re.findall(r'<script>.*?</script>', page, re.S)
cover=re.search(r'<header class="cover">.*?</header>', main, re.S).group(0)
paper=re.search(r'<article>(.*?)</article>', main, re.S).group(1)
appx=re.findall(r'<article>(.*?)</article>', main, re.S)[1]
footer=re.search(r'<footer>.*?</footer>', main, re.S).group(0)
# print colours: keep chart tokens readable on white
tokens='<style>:root{--ink:#111;--ink2:#444;--muted:#777;--rule:#e2e2e2;--panel:#fff;--sans:system-ui,sans-serif;--mono:ui-monospace,Menlo,monospace;--s1:#0b6e6e;--s2:#86b6ef;--s3:#8b8983;--s4:#0b6e6e}</style>'
head=f'<meta charset="utf-8"><title>Own the Knowledge. Rent the Thinking.</title>{tokens}<style>{css}</style>'
# drop the machine-readable blockquote if present in the article
paper=re.sub(r'^\s*<blockquote>\s*<p>This is the machine-readable.*?</blockquote>','',paper,count=1,flags=re.S)
appx=re.sub(r'^\s*<blockquote>\s*<p>This is the machine-readable.*?</blockquote>','',appx,count=1,flags=re.S)
open(f"{S}/print-paper.html","w").write(f'{head}<body>{cover}<article>{paper}</article>{footer}{"".join(scripts)}</body>')
acover=cover.replace('<h1>Own the Knowledge. Rent the Thinking.</h1>','<h1>Appendix A: benchmark methodology</h1>').replace('<p class="sub">Separating institutional understanding from frontier intelligence</p>','<p class="sub">Own the Knowledge. Rent the Thinking. · reference v1.2</p>').replace('<p class="meta muted">Research report</p>','<p class="meta muted">Appendix to the research report</p>')
open(f"{S}/print-appendix.html","w").write(f'{head}<body>{acover}<article>{appx}</article>{footer}{"".join(scripts)}</body>')
for src,out in (("print-paper","acropolis-v1.0"),("print-appendix","acropolis-v1.0-appendix-a")):
    subprocess.run([os.environ.get("CHROME","/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),"--headless=new","--disable-gpu","--no-pdf-header-footer","--virtual-time-budget=8000",f"--print-to-pdf={R}/releases/{out}.pdf",f"file://{S}/{src}.html"],stderr=subprocess.DEVNULL)
    print(out, "ok")
