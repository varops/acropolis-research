"""Vector figures for the paper: one SVG per figure, drawn from the same data as the web charts."""
import os, re, sys, html, importlib.util
S=os.path.dirname(os.path.abspath(__file__)); R=os.path.dirname(S); OUT=f"{R}/paper/figures/svg"
spec=importlib.util.spec_from_file_location("bh", f"{S}/build_html.py")
src=open(f"{S}/build_html.py").read()
CH=eval(src[src.index("CH={"):src.index("def figure(")].split("=",1)[1])  # the chart data dict, verbatim
INK,INK2,MUTED,RULE="#111111","#444444","#777777","#e2e2e2"; SER=["#0b6e6e","#86b6ef","#8b8983"]
F='font-family="Helvetica, Arial, sans-serif"'; M='font-family="Menlo, Consolas, monospace"'
def esc(t): return html.escape(t)
def bars(fid, spec):
    W=760; L=260; Rm=60; T=10; B=34
    if spec["kind"]=="bars":
        rows=[]; 
        for g,items in spec["groups"]:
            rows.append(("head",g)); rows+= [("bar",l,[v]) for l,v in items]
        nser=1; bh=18; gap=6; ggap=14
    else:
        rows=[("bar",l,vals) for l,vals in spec["rows"]]; nser=len(spec["series"]); bh=14; gap=3; ggap=0
    y=T; pos=[]
    for r in rows:
        if r[0]=="head": y+=ggap; pos.append((r,y)); y+=16
        else: pos.append((r,y)); y+= nser*bh+(nser-1)*gap+(6 if spec["kind"]=="bars" else 8)
    H=y+B; x=lambda v: L+(v/spec["max"])*(W-L-Rm)
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {F} font-size="12">']
    for v in (0,25,50,75,100):
        o.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{T}" y2="{H-B+4}" stroke="{RULE}"/><text x="{x(v):.1f}" y="{H-8}" text-anchor="middle" fill="{MUTED}" font-size="11" {M}>{v}</text>')
    o.append(f'<text x="8" y="{H-8}" fill="{MUTED}" font-size="11" {M}>{esc(spec["unit"])}</text>')
    for r,yy in pos:
        if r[0]=="head": o.append(f'<text x="8" y="{yy+12}" fill="{INK2}" font-size="12" font-weight="600">{esc(r[1])}</text>'); continue
        label,vals=r[1],r[2]; rowH=nser*bh+(nser-1)*gap
        o.append(f'<text x="{L-10}" y="{yy+rowH/2+4}" text-anchor="end" fill="{INK}" font-size="12.5">{esc(label)}</text>')
        for i,v in enumerate(vals):
            by=yy+i*(bh+gap); w=max(x(v)-x(0),2)
            o.append(f'<rect x="{x(0):.1f}" y="{by}" width="{w:.1f}" height="{bh}" rx="3" fill="{SER[i]}"/><text x="{x(v)+6:.1f}" y="{by+bh/2+4}" fill="{INK}" font-size="11.5" {M}>{v:.1f}</text>')
    o.append(f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{T}" y2="{H-B+4}" stroke="{MUTED}"/>')
    if spec["kind"]!="bars":
        lx=L
        for i,s in enumerate(spec["series"]):
            o.insert(1, f'<rect x="{lx}" y="{H-B+12}" width="10" height="10" rx="2" fill="{SER[i]}"/><text x="{lx+14}" y="{H-B+21}" fill="{INK2}" font-size="11">{esc(s)}</text>')
            lx+= 14+7*len(s)+18
        # make room for the legend
        o[0]=o[0].replace(f'viewBox="0 0 {W} {H}" width="{W}" height="{H}"', f'viewBox="0 0 {W} {H+16}" width="{W}" height="{H+16}"')
    o.append('</svg>'); open(f"{OUT}/{fid}.svg","w").write("\n".join(o))
def box(o,x,y,w,h,title,sub,inside):
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{"#eef4f3" if inside else "#ffffff"}" stroke="{"#0b6e6e" if inside else "#cfcfcf"}"/>')
    o.append(f'<text x="{x+10}" y="{y+18}" fill="{INK}" font-size="12.5" font-weight="600">{esc(title)}</text>')
    for i,line in enumerate(sub): o.append(f'<text x="{x+10}" y="{y+34+i*13}" fill="{MUTED}" font-size="10.5">{esc(line)}</text>')
def arrow(o,x1,y,x2,dashed=False):
    dash=' stroke-dasharray="4 3"' if dashed else ''
    o.append(f'<line x1="{x1}" y1="{y}" x2="{x2-6}" y2="{y}" stroke="{MUTED}" stroke-width="1.2"{dash}/><path d="M{x2-6},{y-4} L{x2},{y} L{x2-6},{y+4}" fill="none" stroke="{MUTED}" stroke-width="1.2"/>')
def fig1():
    W,H=760,310; o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {F}>']
    o.append(f'<text x="0" y="14" fill="{MUTED}" font-size="10.5" letter-spacing="1" {M}>CONVENTIONAL</text>')
    box(o,0,24,220,64,"Company knowledge",["documents, threads, records, all of it"],False); arrow(o,224,56,266)
    box(o,270,24,220,64,"Frontier AI",["outside the company;","understands and answers"],False); arrow(o,494,56,536)
    box(o,540,24,220,64,"Answer",["an answer, not an asset"],False)
    o.append(f'<text x="0" y="132" fill="{MUTED}" font-size="10.5" letter-spacing="1" {M}>ACROPOLIS</text>')
    box(o,0,142,170,78,"Company",["observations from the","systems it already runs"],True); arrow(o,174,181,206)
    box(o,210,142,250,78,"Owned organizational understanding",["the record: claims, evidence, time, source;","built by a model the company runs"],True); arrow(o,464,181,506)
    box(o,510,142,250,78,"Answer",["local answer seat:","84 to 96% of all-frontier"],True)
    o.append(f'<line x1="335" y1="220" x2="335" y2="262" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="4 3"/>'); arrow(o,335,262,506,True)
    box(o,510,236,250,64,"Frontier reasoning when needed",["sees one question's evidence envelope,","never the record; 96 to 99% of all-frontier"],False)
    o.append(f'<line x1="0" y1="118" x2="{W}" y2="118" stroke="{RULE}"/>')
    o.append('</svg>'); open(f"{OUT}/figure-1-boundary.svg","w").write("\n".join(o))
def fig4():
    W,H=760,250; o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {F}>']
    o.append(f'<text x="0" y="14" fill="{MUTED}" font-size="10.5" letter-spacing="1" {M}>BOLTED-ON: RETRIEVE, STUFF, HOPE</text>')
    steps=[("Retrieve nearest chunks","stale wins if it ranks higher"),("Put them in the prompt","model sees what it should not"),("Instruct the model to behave","policy enforced by the thing being constrained"),("Answer","gaps filled; no provenance survives")]
    x=0
    for i,(t,s) in enumerate(steps):
        box(o,x,24,172,64,t,[s[:34],s[34:]] if len(s)>34 else [s],False)
        if i<3: arrow(o,x+176,56,x+196)
        x+=196
    o.append(f'<text x="0" y="132" fill="{MUTED}" font-size="10.5" letter-spacing="1" {M}>RESIDENT: THE ACROPOLIS REQUEST PATH</text>')
    steps=[("Resolve identity and policy","Eunomia, from the client's directory"),("Retrieve under authorization","Parthenon, before any model runs"),("Assemble task-scoped context","explicit coverage state"),("Plan, act with permission","Hero; Pythia when working out is needed"),("Record an attributable outcome","update versioned state")]
    x=0
    for i,(t,s) in enumerate(steps):
        box(o,x,142,136,72,t if len(t)<=22 else t[:22]+"…",[s[:26],s[26:]] if len(s)>26 else [s],True)
        if i<4: arrow(o,x+140,178,x+156)
        x+=156
    o.append('</svg>'); open(f"{OUT}/figure-4-request-path.svg","w").write("\n".join(o))
def fig5(): bars("figure-5-refusal-dial", CH["fig5"])
def fig9():
    rows=[("Ingest, one time","$8.24","17,745 accepted claims · 37,387 LLM calls"),("Per accepted claim","$0.0021","about $0.24 per million-token conversation"),("Index, one time","$0","72,986 documents embedded, local nomic, CPU only"),("Retrieval, per question","$0.0037","$2.28 for 625 questions"),("Quarantined at the door","0","after the RFC 3339 fix; 5,732 refused before it")]
    W=760; H=len(rows)*54+10; o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {F}>']
    for i,(l,n,d) in enumerate(rows):
        y=i*54
        o.append(f'<text x="0" y="{y+16}" fill="{MUTED}" font-size="11.5">{esc(l)}</text><text x="0" y="{y+40}" fill="{INK}" font-size="20" {M}>{esc(n)}</text><text x="130" y="{y+40}" fill="{INK2}" font-size="12.5">{esc(d)}</text>')
        if i<len(rows)-1: o.append(f'<line x1="0" x2="{W}" y1="{y+50}" y2="{y+50}" stroke="{RULE}"/>')
    o.append('</svg>'); open(f"{OUT}/figure-9-cost-of-record.svg","w").write("\n".join(o))
fig1(); bars("figure-2-placement",CH["fig2"]); bars("figure-3-beam100k-by-ability",CH["fig3"]); fig4(); fig5(); bars("figure-6-retrieval",CH["fig6"]); bars("figure-7-longmemeval-answering",CH["fig7"]); bars("figure-8-beam1m-composite",CH["fig8"]); fig9()
print(sorted(os.listdir(OUT)))
