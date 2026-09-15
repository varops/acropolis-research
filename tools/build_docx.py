"""Word editions: the Markdown with each Mermaid figure replaced by its SVG, through pandoc."""
import os, re, subprocess
S=os.path.dirname(os.path.abspath(__file__)); R=os.path.dirname(S); os.makedirs(f"{S}/out", exist_ok=True)
svgs={1:"figure-1-boundary",2:"figure-2-placement",3:"figure-3-beam100k-by-ability",4:"figure-4-request-path",5:"figure-5-refusal-dial",6:"figure-6-retrieval",7:"figure-7-longmemeval-answering",8:"figure-8-beam1m-composite",9:"figure-9-cost-of-record"}
def prep(src):
    s=open(src).read()
    s=re.sub(r'^> This is the machine-readable version.*?\n\n','',s,count=1,flags=re.S|re.M)
    def sub(m):
        cap=m.group(1); n=int(re.match(r'Figure (\d+)',cap).group(1))
        return f'![{cap}]({R}/paper/figures/svg/{svgs[n]}.svg)\n\n'
    # "**Figure N. title.** note Source: ...\n\n```mermaid...```" -> image with the caption
    s=re.sub(r'\*\*(Figure \d+\..*?)\*\*.*?\n\n```mermaid\n.*?```\n\n', sub, s, flags=re.S)
    return s
for src,out in (("paper/README.md","acropolis-v1.0"),("paper/methodology.md","acropolis-v1.0-appendix-a")):
    tmp=f"{S}/{out}.docx.md"; open(tmp,"w").write(prep(f"{R}/{src}"))
    subprocess.run(["pandoc",tmp,"-f","gfm","-t","docx","--resource-path",f"{R}/paper","-o",f"{S}/out/{out}.docx"],check=True)
    os.remove(tmp); print(out+".docx")
