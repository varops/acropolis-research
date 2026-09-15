import re, html, json
import os; S=os.path.dirname(os.path.abspath(__file__))
R=os.path.dirname(S)
paper=open(f"{S}/paper-body.html").read(); app=open(f"{S}/appendix-body.html").read()

# ---- figure definitions (data verbatim from the paper) ----
CH={
 "fig2": {"kind":"bars","title":"Share of the all-frontier score, by placement","unit":"% of reference","max":100,
   "groups":[["LongMemEval-S",[["own everything",95.6],["rent the thinking",98.5],["rent on refusals",96.9]]],
             ["LoCoMo",[["own everything",93.3],["rent the thinking",96.9],["rent on refusals",98.4]]],
             ["BEAM 100K, strict",[["own everything",84.0],["rent the thinking",95.7],["rent on refusals",86.3]]],
             ["BEAM 100K, own protocol",[["own everything",84.9],["rent the thinking",98.4]]]]},
 "fig3": {"kind":"grouped","title":"BEAM 100K by ability, BEAM's own protocol (mean of 40)","unit":"mean rubric score","max":100,
   "series":["own everything (local loop)","rent the thinking","frontier in every seat, same brains"],
   "rows":[["extraction",[70.8,89.1,86.4]],["preference",[94.1,87.8,87.9]],["instruction",[72.8,90.9,92.1]],["knowledge update",[59.7,57.9,62.5]],["contradiction",[52.7,67.5,67.5]],["temporal",[66.7,78.6,80.7]],["multi-session",[60.3,58.0,55.1]],["summarization",[23.8,36.9,36.3]],["event ordering",[16.5,32.9,34.6]]]},
 "fig5": {"kind":"grouped","title":"Refusal posture: two calibrations of one contract","unit":"percent","max":100,
   "series":["LongMemEval accuracy","BEAM abstention"],
   "rows":[["synthesis-forward",[90.5,50.0]],["balanced",[89.4,64.3]]]},
 "fig6": {"kind":"grouped","title":"Retrieval, identity-scored","unit":"% of questions","max":100,
   "series":["Hit@5","Hit@10"],
   "rows":[["LongMemEval-S, frontier",[99.0,99.8]],["LoCoMo, frontier",[90.74,93.06]],["BEAM 1M, frontier",[35.84,44.0]],["LongMemEval-S, local brains, local rerank",[99.4,99.6]],["LoCoMo, local brains, local rerank",[80.6,85.2]],["LoCoMo, local brains, frontier rerank",[91.2,92.6]],["BEAM 100K, published brains",[40.6,49.6]],["BEAM 100K, local brains, frontier rerank",[39.2,47.3]],["BEAM 100K, local brains, local rerank",[33.8,43.9]]]},
 "fig7": {"kind":"bars","title":"LongMemEval-S accuracy, 500 questions","unit":"accuracy","max":100,
   "groups":[["Acropolis, published configuration",[["core",89.2],["agentic (Pythia)",90.5],["agentic + frontier escalation",91.6]]],
             ["Acropolis, local brains",[["rented answer seat",90.0]]],
             ["Same system, never-refuse probe",[["all 500 questions",87.2],["470 answerable only",92.8]]],
             ["Vendor X, never-refuse protocol",[["as published",98.0]]]]},
 "fig8": {"kind":"grouped","title":"BEAM 1M per category, official rubric protocol","unit":"score","max":100,
   "series":["Acropolis governed composite","Vendor X, published"],
   "rows":[["abstention",[75.7,52.5]],["contradiction",[62.1,35.7]],["summarization",[56.4,63.5]],["multi-session",[57.9,65.2]]]},
}
def figure(num, title, inner, caption=""):
    return f'<figure class="fig" id="figure-{num}"><figcaption><span class="fig-no">Figure {num}</span> {html.escape(title)}</figcaption>{inner}{("<p class=cap>"+caption+"</p>") if caption else ""}</figure>'
def chart(fid): return f'<div class="chart" data-chart="{fid}"><canvas></canvas></div>'
FLOW1='''<div class="flow"><div class="path"><h4>Conventional</h4><div class="steps"><div class="step">Company knowledge<small>documents, threads, records, all of it</small></div><span class="arrow">→</span><div class="step">Frontier AI<small>outside the company; understands and answers</small></div><span class="arrow">→</span><div class="step">Answer<small>an answer, not an asset</small></div></div></div>
<div class="path"><h4>Acropolis</h4><div class="steps"><div class="step in">Company<small>observations from the systems it already runs</small></div><span class="arrow">→</span><div class="step in">Owned organizational understanding<small>the record: claims, evidence, time, source; built by a model the company runs</small></div><span class="arrow">→</span><div class="step in">Answer<small>local answer seat: 84 to 96% of all-frontier</small></div><span class="arrow">⤷</span><div class="step">Frontier reasoning when needed<small>sees one question's evidence envelope, never the record; 96 to 99% of all-frontier</small></div></div><p class="note">The boundary: the record never crosses it. An evidence envelope of a few thousand tokens can, one question at a time, and it is logged with the answer.</p></div></div>'''
FLOW4='''<div class="flow"><div class="path"><h4>Bolted-on: retrieve, stuff, hope</h4><div class="steps"><div class="step">Retrieve nearest chunks<small>stale wins if it ranks higher</small></div><span class="arrow">→</span><div class="step">Put them in the prompt<small>model sees what it should not</small></div><span class="arrow">→</span><div class="step">Instruct the model to behave<small>policy enforced by the thing being constrained</small></div><span class="arrow">→</span><div class="step">Answer<small>gaps filled; no provenance survives</small></div></div></div>
<div class="path"><h4>Resident: the Acropolis request path</h4><div class="steps"><div class="step in">Resolve identity and policy<small>Eunomia, from the client's directory</small></div><span class="arrow">→</span><div class="step in">Retrieve under that authorization<small>Parthenon, before any model runs</small></div><span class="arrow">→</span><div class="step in">Assemble task-scoped context<small>explicit coverage state</small></div><span class="arrow">→</span><div class="step in">Plan, act with permission<small>Hero; Pythia when working out is needed</small></div><span class="arrow">→</span><div class="step in">Record an attributable outcome<small>update versioned state</small></div></div></div></div>'''
TILES9='''<div class="tiles"><div class="tile"><span>Ingest, one time</span><b>$8.24</b><small>17,745 accepted claims · 37,387 LLM calls</small></div><div class="tile"><span>Per accepted claim</span><b>$0.0021</b><small>about $0.24 per million-token conversation</small></div><div class="tile"><span>Index, one time</span><b>$0</b><small>72,986 documents embedded, local nomic, CPU only</small></div><div class="tile"><span>Retrieval, per question</span><b>$0.0037</b><small>$2.28 for 625 questions</small></div><div class="tile"><span>Quarantined at the door</span><b>0</b><small>after the RFC 3339 fix; 5,732 refused before it</small></div></div>'''
FIGS={
 1:("The brain stays inside; a question-sized envelope can leave", FLOW1, ""),
 2:("Own the knowledge, rent the thinking: how much frontier you get without a frontier brain", chart("fig2"), "Reference: a frontier model in every seat on the published brains. Local is Gemma-4-31B on one H200 with local embeddings."),
 3:("BEAM 100K by ability: what renting the answer seat buys back", chart("fig3"), "Overall under the protocol: 57.3, 66.4, 66.8."),
 4:("Bolted-on retrieval and the resident request path, step by step", FLOW4, ""),
 5:("Refusal posture is a dial with two measured endpoints", chart("fig5"), "Moving from synthesis-forward to balanced buys 14.3 points of BEAM abstention for 1.1 points of LongMemEval accuracy."),
 6:("Retrieval holds to a million tokens, then meets the cliff every published figure shows", chart("fig6"), "The first three rows are the frontier configuration; the rest are the September local-brain rows."),
 7:("LongMemEval answering: the published rows, the local-brain row, the never-refuse probe, and a comparison that cannot lose points for refusing", chart("fig7"), "Vendor X's protocol cannot lose points for refusing; 30 of the 500 questions are unanswerable traps, so a never-refuse system caps at 94.0 under the official rule."),
 8:("BEAM 1M per category: where the governed composite leads and where it trails", chart("fig8"), "Overall is stated only as a paired delta (+3.5 over its paired core); cross-formula absolutes are not valid."),
 9:("The cost of record: BEAM 1M, 35 conversations, about 35 million tokens", TILES9, "Two Xeon 8280s, 16 cores, 31 GB, no GPU. Measured on the 2026-08-20 ingest."),
}
# replace mermaid blocks (in document order 1,2,3,4,5,6,7,8,9) with figures; drop the "**Figure N. ...** Source:" paragraphs preceding them
order=[1,2,3,4,5,6,7,8,9]; i=0
def sub(m):
    global i
    n=order[i]; i+=1; t,inner,cap=FIGS[n]; return figure(n,t,inner,cap)
paper=re.sub(r'<pre class="mermaid">.*?</pre>', sub, paper, flags=re.S)
paper=re.sub(r'<p><strong>Figure \d+\..*?</p>\n?', '', paper, flags=re.S)
# tables: mark
for b in (paper, app): pass
# title block: first h1/h2/h3 + the paragraph lines
m=re.match(r'\s*<h1[^>]*>(.*?)</h1>\s*<h2[^>]*>(.*?)</h2>\s*<h3[^>]*>(.*?)</h3>\s*<p>(.*?)</p>\s*<p>(.*?)</p>\s*<blockquote>.*?</blockquote>', paper, flags=re.S)
title, sub_, series, meta, kind = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
# the author block, line by line from the Markdown source (pandoc reflows the paragraph)
md=open(f'{R}/paper/README.md').read().split('\n'); i=[k for k,l in enumerate(md) if l.startswith('### ')][0]+2
lines=[]
while i<len(md) and md[i].strip(): lines.append(re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html.escape(md[i].strip()))); i+=1
meta='<br>'.join(lines)
paper=paper[m.end():]
paper=re.sub(r'<p>Figures: <code>figures/acropolis-figures.html</code>\..*?</p>','',paper,count=1,flags=re.S)
# ids for h2 and build nav
def slug(t): return re.sub(r'[^a-z0-9]+','-',re.sub(r'<[^>]+>','',t).lower()).strip('-')
nav=[]
def addids(body, prefix):
    def r(m):
        t=m.group(2); s=prefix+slug(t); nav.append((prefix, s, re.sub(r'<[^>]+>','',t))); return f'<h2 id="{s}">{t}</h2>'
    return re.sub(r'<h2([^>]*)>(.*?)</h2>', r, body, flags=re.S)
paper=addids(paper,"p-"); app=addids(app,"a-")
app=re.sub(r'^\s*<h1[^>]*>.*?</h1>\s*<h3[^>]*>.*?</h3>\s*<blockquote>.*?</blockquote>','',app,count=1,flags=re.S)
def tocselect():
    opts=''.join(f'<option value="{s}">{("A. " if p=="a-" else "")}{html.escape(t)}</option>' for p,s,t in nav)
    return f'<select class="toc-select" aria-label="Contents" onchange="if(this.value)location.hash=this.value"><option value="">Contents</option>{opts}</select>'
def navlist(prefix):
    items=[f'<a href="#{s}">{html.escape(t)}</a>' for p,s,t in nav if p==prefix]
    return "".join(items)
css=open(f"{S}/site.css").read(); js=open(f"{S}/charts.js").read()
paper=re.sub(r'<table>(\s*<thead>\s*<tr[^>]*>\s*<th[^>]*>property or path</th>.*?)</table>', r'<table class="evidence">\1</table>', paper, count=1, flags=re.S); paper=re.sub(r'<table>(.*?)</table>', r'<div class="tbl"><table>\1</table></div>', paper, flags=re.S); paper=re.sub(r'<table class="evidence">(.*?)</table>', r'<div class="tbl"><table class="evidence">\1</table></div>', paper, flags=re.S); app=re.sub(r'<table>(\s*<thead>\s*<tr[^>]*>\s*<th[^>]*>path</th>.*?)</table>', r'<table class="firstwide wrapfirst">\1</table>', app, flags=re.S); app=re.sub(r'<table>(\s*<thead>\s*<tr[^>]*>\s*<th[^>]*>(?:dataset|seat|date)</th>.*?)</table>', r'<table class="firstwide">\1</table>', app, flags=re.S); app=re.sub(r'<table>(.*?)</table>', r'<div class="tbl"><table>\1</table></div>', app, flags=re.S); app=re.sub(r'<table class="(firstwide(?: wrapfirst)?)">(.*?)</table>', r'<div class="tbl"><table class="\1">\2</table></div>', app, flags=re.S)
kicker=re.sub(r'\s*·\s*Technical Report 01\s*$','',series)
page=f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Own the Knowledge, Rent the Thinking.</title>
<style>{css}</style>
<div class="layout">
<nav class="side"><div class="brand"><a href="#top">Table of Contents</a></div>{tocselect()}
<div class="group">Report</div>{navlist("p-")}
<div class="group">Appendix A</div>{navlist("a-")}
<div class="group">Evidence</div><a href="https://github.com/varops/acropolis-research">Reports, manifests, reproduction ↗</a>
</nav>
<main class="doc" id="top">
<header class="cover"><p class="logo"><svg viewBox="0 0 87.4 45.1" xmlns="http://www.w3.org/2000/svg" style="width:88px; height: 45px;" role="img" aria-label="VarOps"><path d="m10.8 2.2c-1.1 1.7-1.5 5 0 9.2l8.5 22.9 7.6-20.5c2.3-6.2 1.2-9.7-.1-11.5 0-.1 8.3-.1 8.3-.1-2.4 2.8-3.5 5-5.1 9.4l-11.4 30.8h-2.2l-11.5-31.2c-1.8-4.9-3-6.8-4.9-8.9 0-.1 10.9-.1 10.9-.1z"></path><path d="m43.5.1 1.3 1.6c-1.8 1.6-3.5 3.9-5.1 7.1-2.2 4.3-3.3 8.9-3.3 13.8s1.3 10.1 3.8 14.7c1.5 2.7 3 4.8 4.6 6.2l-1.3 1.6c-7.3-6.4-10.9-13.9-10.9-22.4s3.6-16.1 10.9-22.5z"></path><path d="m41.8 22.2c0-11.6 8.9-20.8 18.3-20.8s18.4 9.2 18.4 20.8-9 20.6-18.4 20.6-18.3-9.1-18.3-20.6zm30.8 0c0-10.5-4.7-18.6-12.5-18.6s-12.5 8.1-12.5 18.6 4.7 18.5 12.5 18.5 12.5-8 12.5-18.5z"></path><path d="m76.5.1c7.3 6.4 10.9 13.9 10.9 22.5s-3.6 16.1-10.9 22.4l-1.3-1.6c1.8-1.6 3.5-3.9 5.1-7.1 2.2-4.3 3.3-8.9 3.3-13.8s-1.3-10.1-3.8-14.7c-1.5-2.7-3.1-4.8-4.6-6.2l1.3-1.6v.1z"></path></svg></p><p class="kicker">{kicker}</p><h1>{title}</h1><p class="sub">{sub_}</p><p class="meta">{meta}</p><p class="links"><a href="https://varops.com/acropolis">website</a><span>|</span><a href="https://github.com/varops/acropolis-research">github</a><span>|</span><a href="mailto:research@varops.com">contact</a></p><p class="meta muted">{kind}</p></header>
<article>{paper}</article>
<hr class="part">
<header class="cover small"><p class="kicker">Appendix A</p><h1>Benchmark methodology</h1></header>
<article>{app}</article>
<footer>Own the Knowledge, Rent the Thinking. · Acropolis, a governed model of the organization · Technical Report 01 · VarOps LLC, September 2026, version 1.0 · CC BY 4.0 · <a href="https://github.com/varops/acropolis-research">varops/acropolis-research</a></footer>
</main></div>
<script>const CHARTS={json.dumps(CH)};</script>
<script>{js}</script>
'''
open(f"{R}/paper/index.html","w").write(page); print("written", len(page)//1024, "KB; nav", len(nav))
