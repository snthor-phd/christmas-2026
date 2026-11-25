#!/usr/bin/env python3
"""Build the Christmas 2026 site from data/gifts.json and decks/<id>/.

Outputs (repo root):
  index.html                 landing page
  gift-list.html             compact shopping list
  gift-list.pdf              same list, letter size (needs Playwright)
  decks/<id>/index.html      standalone deck viewer for claude.ai-style slide decks

Usage:  uv run --with playwright tools/build.py   (HTML + PDF)
        python3 tools/build.py --no-pdf               (HTML only)
"""
import html, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://snthor-phd.github.io/christmas-2026/"  # live site, used for links inside the PDF
DATA = json.loads((ROOT / "data/gifts.json").read_text())
E = html.escape

def head(prefix=""):
    return ('<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow">'
            f'<link rel="stylesheet" href="{prefix}assets/fonts.css">')
HEAD = head()

PALETTE = """
:root{--paper:#F6EFE0;--card:#FFFDF8;--ink:#12372A;--muted:#5C6B61;--rule:#E3D9C4;
--red:#B8322F;--green:#1F5C45;--gold:#C89B3C}
"""

def money(x):
    if x is None: return ""
    if x >= 10000: return f"${x/1000:,.0f}K"
    return f"${x:,.2f}".replace(".00", "")

def price_cell(g):
    if g.get("price_text"): return g["price_text"]
    if g.get("price_hi"): return f"{money(g['price'])}–{money(g['price_hi'])}"
    return money(g.get("price"))

def totals(p):
    lo = hi = 0.0
    for g in p.get("gifts", []):
        if g.get("dream") or g.get("homemade") or g.get("price") is None: continue
        lo += g["price"]; hi += g.get("price_hi") or g["price"]
    return lo, hi

def total_text(lo, hi):
    a = f"${lo:,.0f}"
    return a if round(hi) == round(lo) else f"{a}–${hi:,.0f}"

def links_html(links):
    return " · ".join(f'<a href="{E(l["url"])}" target="_blank" rel="noopener">{E(l["label"])}</a>'
                      for l in links or [])

def date_text(iso):
    import datetime
    d = datetime.date.fromisoformat(iso)
    return f"{d:%b} {d.day}, {d.year}"

people = DATA["people"]
real = [p for p in people if not p.get("placeholder")]

# ---------------------------------------------------------------- deck viewers
VIEWER = """<!doctype html><html lang="en"><head>__HEAD__<title>__TITLE__</title><style>
html,body{margin:0;height:100%;background:#0E2A20;overflow:hidden;font-family:'Nunito Sans',Arial,sans-serif}
#stage{position:absolute;left:50%;top:50%;width:1920px;height:1080px;transform-origin:0 0}
#stage>section{position:absolute;inset:0;width:1920px;height:1080px;box-sizing:border-box;overflow:hidden}
#stage>section:not(.on){display:none!important}
#stage section *{margin:0;box-sizing:border-box}
#stage section aside{display:none}
#bar{position:fixed;left:0;right:0;bottom:0;display:flex;align-items:center;gap:8px;padding:8px 12px;
 background:rgba(14,42,32,.86);color:#F6EFE0;font-size:14px;z-index:5}
#bar a,#bar button{color:#F6EFE0;background:none;border:1px solid rgba(246,239,224,.35);border-radius:6px;
 padding:6px 12px;font:inherit;cursor:pointer;text-decoration:none}
#bar button:disabled{opacity:.35;cursor:default}
#count{min-width:64px;text-align:center}
#notes{position:fixed;left:12px;right:12px;bottom:52px;max-height:30vh;overflow:auto;background:#FFFDF8;color:#12372A;
 border-radius:10px;padding:12px 16px;font-size:15px;line-height:1.45;display:none;z-index:4;box-shadow:0 6px 24px rgba(0,0,0,.35)}
#notes.on{display:block}
.sp{flex:1}
</style></head><body>
<div id="stage">__SLIDES__</div>
<div id="notes"></div>
<div id="bar"><a href="../../">&#8962; Home</a><a href="../../gift-list.html#__ID__">Gift list</a><span class="sp"></span>
<button id="prev" aria-label="Previous slide">&#8592;</button><span id="count"></span>
<button id="next" aria-label="Next slide">&#8594;</button><span class="sp"></span><button id="nbtn">Notes</button></div>
<script>
const S=[...document.querySelectorAll('#stage>section')],st=document.getElementById('stage'),
 cnt=document.getElementById('count'),nt=document.getElementById('notes');
let i=0;
document.querySelectorAll('#stage a[href]').forEach(a=>{a.target='_blank';a.rel='noopener'});
function fit(){const barH=52,w=innerWidth,h=innerHeight-barH,s=Math.min(w/1920,h/1080);
 st.style.transform=`translate(${-960*s}px,${-540*s-barH/2}px) scale(${s})`}
function show(n){i=Math.max(0,Math.min(S.length-1,n));S.forEach((x,k)=>x.classList.toggle('on',k===i));
 cnt.textContent=(i+1)+' / '+S.length;document.getElementById('prev').disabled=i===0;
 document.getElementById('next').disabled=i===S.length-1;
 const a=S[i].querySelector('aside');nt.textContent=a?a.textContent:'No notes on this slide.';
 history.replaceState(null,'','#'+(i+1))}
document.getElementById('prev').onclick=()=>show(i-1);
document.getElementById('next').onclick=()=>show(i+1);
document.getElementById('nbtn').onclick=()=>nt.classList.toggle('on');
addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){show(i+1);e.preventDefault()}
 if(['ArrowLeft','PageUp'].includes(e.key))show(i-1);if(e.key==='n'||e.key==='N')nt.classList.toggle('on');
 if(e.key==='Home')show(0);if(e.key==='End')show(S.length-1)});
let x0=null;addEventListener('touchstart',e=>{x0=e.touches[0].clientX},{passive:true});
addEventListener('touchend',e=>{if(x0===null)return;const d=e.changedTouches[0].clientX-x0;
 if(Math.abs(d)>40)show(i+(d<0?1:-1));x0=null});
addEventListener('resize',fit);fit();show((parseInt(location.hash.slice(1))||1)-1);
</script></body></html>"""

for p in real:
    d = ROOT / p["deck"]
    meta = d / "deck.json"
    if meta.exists():  # claude.ai slide deck: HTML fragments in slides/
        deck = json.loads(meta.read_text())
        title = deck["title"]
        slides = "\n".join((d / "slides" / f"{sid}.html").read_text() for sid in deck["order"])
    else:  # PowerPoint / PDF / Keynote export: one image per slide in slides/
        imgs = sorted(f for f in (d / "slides").glob("*") if f.suffix.lower() in (".png", ".jpg", ".jpeg"))
        if not imgs:
            continue
        title = f"{p['name']}'s Christmas List"
        slides = "\n".join(f'<section style="display:flex;background:#fff"><img src="slides/{f.name}" alt="Slide {k+1}" '
                           f'style="width:100%;height:100%;object-fit:contain"></section>' for k, f in enumerate(imgs))
    out = (VIEWER.replace("__HEAD__", head("../../")).replace("__TITLE__", E(f"{p['name']} · {title}"))
           .replace("__SLIDES__", slides).replace("__ID__", p["id"]))
    (d / "index.html").write_text(out)

# ---------------------------------------------------------------- gift list
LIST_CSS = PALETTE + """
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.35 'Nunito Sans',Arial,sans-serif}
main{max-width:980px;margin:0 auto;padding:20px 16px 48px}
h1{font:600 30px/1.1 'Fredoka',Arial,sans-serif;margin:0}
.top{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 16px;border-bottom:2px solid var(--ink);padding-bottom:8px}
.top .meta{color:var(--muted);font-size:13px}
.top .dl{margin-left:auto;font-size:13px}
nav.jump{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 4px}
nav.jump a{font-size:13px;padding:3px 10px;border:1px solid var(--rule);border-radius:999px;background:var(--card);color:var(--ink);text-decoration:none}
.rule{font-size:12.5px;color:var(--muted);margin:6px 0 0}
section.person{margin-top:18px;break-inside:auto}
.ph{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px;border-bottom:1px solid var(--ink);padding-bottom:3px}
.ph h2{font:600 21px/1.1 'Fredoka',Arial,sans-serif;margin:0}
.ph .who{font-size:12.5px;color:var(--red);font-weight:700}
.ph .tot{margin-left:auto;font-size:13px;font-weight:700}
.ph .tot span{font-weight:400;color:var(--muted)}
.ph a.deck{font-size:12.5px}
table{width:100%;border-collapse:collapse;margin-top:2px}
th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:700;text-align:left;padding:4px 6px;border-bottom:1px solid var(--rule)}
td{padding:5px 6px;border-bottom:1px solid var(--rule);vertical-align:top}
td.n{width:30px;color:var(--muted);font-size:12px}
td.n a{color:var(--muted)}
td.g b{font-weight:700}
td.g .d{color:var(--muted);font-size:12.5px}
td.g .note{font-size:12px;color:var(--ink);font-style:italic}
td.p{white-space:nowrap;text-align:right;font-variant-numeric:tabular-nums;width:120px}
td.l{width:150px;font-size:13px}
td.r{width:62px;font-size:12px;font-weight:700;color:var(--red)}
th.p{text-align:right}
a{color:var(--green)}
tr.dream td{background:#FBF3DF}
tr.home td.p{color:var(--muted)}
h3{font:700 12px/1 'Nunito Sans',Arial,sans-serif;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:10px 0 2px}
tr.x td{padding:3px 6px;font-size:13px}
.grp{font-size:11.5px;white-space:nowrap;width:76px}
.grp a{color:var(--muted)}
table.extras td.l:empty,table.extras td.r:empty{padding:0}
.empty{color:var(--muted);font-size:13px;padding:6px 0}
.dnb{margin:6px 0 2px;padding:5px 8px;background:#F8E3E1;border-left:3px solid var(--red);font-size:13px}
.dnb b{color:var(--red)}
.pnote{margin:4px 0 0;font-size:12.5px;color:var(--muted)}
footer{margin-top:24px;font-size:12px;color:var(--muted);border-top:1px solid var(--rule);padding-top:8px}
@media (max-width:640px){
 table,tbody,tr,td{display:block;width:auto}
 thead{display:none}
 tr{display:grid;grid-template-columns:28px 1fr auto;column-gap:8px;padding:7px 0;border-bottom:1px solid var(--rule)}
 td{border:0;padding:0}
 td.n{grid-row:1/3}
 td.g{grid-column:2}
 td.p{grid-column:3;grid-row:1;width:auto}
 td.l{grid-column:2/4;width:auto;margin-top:2px}
 td.r{grid-column:3;grid-row:2;width:auto;text-align:right}
 td.r:empty{display:none}
 tr.x{grid-template-columns:70px 1fr auto;padding:4px 0}
 tr.x td.l,tr.x td.r{display:none}
 .ph .tot{margin-left:0;width:100%}
}
@media print{
 @page{size:letter;margin:.45in .5in}
 body{background:#fff;font-size:10.5px}
 main{max-width:none;padding:0}
 h1{font-size:22px}
 nav.jump,.top .dl,.ph a.deck{display:none}
 .ph h2{font-size:16px}
 td{padding:3px 5px}
 td.g .d,td.g .note,td.n,td.l,td.r,tr.x td{font-size:9.5px}
 td.l{width:120px} td.p{width:100px}
 tr{break-inside:avoid}
 .dnb{-webkit-print-color-adjust:exact;print-color-adjust:exact;font-size:10px}
 .pnote{font-size:9.5px}
 .ph{break-after:avoid}
 a{color:var(--green);text-decoration:none}
 tr.dream td{background:#FBF3DF;-webkit-print-color-adjust:exact;print-color-adjust:exact}
 section.placeholders{display:none}
}
"""

def gift_rows(p):
    base = p["deck"]
    rows = []
    for g in p.get("gifts", []):
        cls = "dream" if g.get("dream") else ("home" if g.get("homemade") else "")
        note = f'<div class="note">{E(g["note"])}</div>' if g.get("note") else ""
        det = f'<div class="d">{E(g["detail"])}</div>' if g.get("detail") else ""
        rows.append(
            f'<tr class="{cls}"><td class="n"><a href="{base}#{g["slide"]}" title="Open slide {g["slide"]}">{g["slide"]}</a></td>'
            f'<td class="g"><b>{E(g["gift"])}</b>{det}{note}</td>'
            f'<td class="p">{E(price_cell(g))}</td><td class="l">{links_html(g.get("links"))}</td>'
            f'<td class="r">{E(g.get("priority",""))}</td></tr>')
    return "\n".join(rows)

def extras_block(p):
    ex = p.get("extras")
    if not ex: return ""
    rows = "\n".join(
        f'<tr class="x"><td class="grp"><a href="{p["deck"]}#{x["slide"]}">{E(x.get("group",""))}</a></td><td class="g">{E(x["gift"])}'
        f'{" — " + links_html(x.get("links")) if x.get("links") else ""}</td>'
        f'<td class="p">{E(x.get("price_text",""))}</td><td class="l"></td><td class="r"></td></tr>' for x in ex)
    slides = sorted({x["slide"] for x in ex})
    sl = (f' (<a href="{p["deck"]}#{slides[0]}">slide {slides[0]}</a>)' if len(slides) == 1 else "")
    return (f'<h3>{E(p.get("extras_title","Also welcome"))}{sl}</h3>'
            f'<table class="extras"><tbody>{rows}</tbody></table>')

def person_block(p):
    lo, hi = totals(p)
    n = len(p.get("gifts", []))
    excl = []
    if any(g.get("dream") for g in p["gifts"]): excl.append("dream gift")
    if any(g.get("homemade") for g in p["gifts"]): excl.append("homemade")
    unpriced = sum(1 for g in p["gifts"] if g.get("price") is None and not g.get("dream") and not g.get("homemade"))
    if unpriced: excl.append(f"{unpriced} unpriced")
    ex = f' <span>(excl. {", ".join(excl)})</span>' if excl else ""
    dnb = (f'<p class="dnb"><b>Please don\'t buy:</b> {E(", ".join(p["do_not_buy"]))}'
           f' (<a href="{p["deck"]}#{p.get("do_not_buy_slide","")}">slide {p.get("do_not_buy_slide","")}</a>)</p>'
           if p.get("do_not_buy") else "")
    intro = f'<p class="pnote">{E(p["note"])}</p>' if p.get("note") else ""
    return f"""<section class="person" id="{p['id']}">
<div class="ph"><h2>{E(p['name'])}</h2><span class="who">Before buying, check with {E(p['coordinator'])}</span>
<a class="deck" href="{p['deck']}">Open deck ›</a>
<span class="tot">{n} gifts · {total_text(lo, hi)}{ex}</span></div>
{dnb}{intro}
<table><thead><tr><th>#</th><th>Gift</th><th class="p">Price</th><th>Shop</th><th>Priority</th></tr></thead>
<tbody>{gift_rows(p)}</tbody></table>
{extras_block(p)}
</section>"""

grand_lo = sum(totals(p)[0] for p in real); grand_hi = sum(totals(p)[1] for p in real)
pending = [p for p in people if p.get("placeholder")]
asof = sorted({p["prices_as_of"] for p in real})
gift_list = f"""<!doctype html><html lang="en"><head>{HEAD}<title>Gift List · {E(DATA['title'])}</title>
<style>{LIST_CSS}</style></head><body><main>
<div class="top"><h1>{E(DATA['title'])} Gift List</h1>
<span class="meta">{len(real)} of {len(people)} lists in · {sum(len(p['gifts']) for p in real)} gifts · about {total_text(grand_lo, grand_hi)}</span>
<span class="dl"><a href="./">Home</a> · <a href="gift-list.pdf">PDF</a></span></div>
<nav class="jump">{''.join(f'<a href="#{p["id"]}">{E(p["name"])}</a>' for p in real)}</nav>
<p class="rule">Prices as of {", ".join(date_text(a) for a in asof)}; they'll move with holiday sales. Slide # opens the matching slide in that person's deck. To keep surprises, tell the listed person before you buy, never the recipient.</p>
{''.join(person_block(p) for p in real)}
{f'<section class="person placeholders"><div class="ph"><h2>Still to come</h2></div><p class="empty">{len(pending)} more {"list" if len(pending)==1 else "lists"} will appear here as their decks arrive.</p></section>' if pending else ''}
<footer>Updated {date_text(DATA['updated'])}. Built from data/gifts.json by tools/build.py.</footer>
</main></body></html>"""
(ROOT / "gift-list.html").write_text(gift_list)

# ---------------------------------------------------------------- landing page
IDX_CSS = PALETTE + """
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.45 'Nunito Sans',Arial,sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 16px 48px}
h1{font:600 clamp(34px,7vw,56px)/1 'Fredoka',Arial,sans-serif;margin:0}
.sub{color:var(--muted);margin:8px 0 0}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0 26px}
.cta a{display:inline-block;padding:10px 18px;border-radius:999px;font-weight:700;text-decoration:none}
.cta .pri{background:var(--red);color:#FFFDF8}
.cta .sec{border:2px solid var(--ink);color:var(--ink)}
h2{font:600 22px/1 'Fredoka',Arial,sans-serif;margin:0 0 10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--rule);border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:4px}
.card h3{font:600 20px/1.1 'Fredoka',Arial,sans-serif;margin:0}
.card .m{color:var(--muted);font-size:13px}
.card .links{margin-top:auto;padding-top:8px;display:flex;gap:12px;font-weight:700;font-size:14px}
.card a{color:var(--green)}
.card.soon{background:transparent;border-style:dashed}
.card.soon h3{color:var(--muted)}
footer{margin-top:28px;font-size:12.5px;color:var(--muted)}
"""
def card(k, p):
    if p.get("placeholder"):
        return f'<div class="card soon"><h3>List {k}</h3><span class="m">Coming soon</span></div>'
    lo, hi = totals(p)
    return (f'<div class="card"><h3>{E(p["name"])}</h3><span class="m">{len(p["gifts"])} gifts · {E(p.get("theme",""))} deck</span>'
            f'<span class="m">Before buying, check with {E(p["coordinator"])}</span>'
            f'<div class="links"><a href="{p["deck"]}">Deck ›</a><a href="gift-list.html#{p["id"]}">Gifts ›</a></div></div>')
index = f"""<!doctype html><html lang="en"><head>{HEAD}<title>{E(DATA['title'])}</title><style>{IDX_CSS}</style></head>
<body><main><h1>{E(DATA['title'])}</h1>
<p class="sub">Everyone's wish lists in one place: open a deck to see the gifts, or use the gift list to shop.</p>
<div class="cta"><a class="pri" href="gift-list.html">Gift list</a><a class="sec" href="gift-list.pdf">Gift list (PDF)</a></div>
<h2>Wish lists</h2><div class="grid">{''.join(card(k+1, p) for k, p in enumerate(people))}</div>
<footer>Updated {date_text(DATA['updated'])}. Shhh: tell the listed person before you buy, never the recipient.</footer>
</main></body></html>"""
(ROOT / "index.html").write_text(index)

# ---------------------------------------------------------------- PDF
if "--no-pdf" not in sys.argv:
    # Needs Playwright:  uv run --with playwright tools/build.py   (first time: playwright install chromium)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception:
            browser = pw.chromium.launch(channel="chrome")  # fall back to installed Google Chrome
        # PDF copy: point slide/deck links at the live site so they work from a downloaded file
        tmp = ROOT / "_print.html"
        tmp.write_text(gift_list.replace('href="decks/', f'href="{SITE}decks/'))
        page = browser.new_page()
        page.goto(tmp.as_uri(), wait_until="load", timeout=30000)
        page.pdf(path=str(ROOT / "gift-list.pdf"), format="Letter", print_background=True,
                 prefer_css_page_size=True)
        browser.close()
        tmp.unlink()
print("built:", ", ".join(p["id"] for p in real), "| grand total", total_text(grand_lo, grand_hi))
