#!/usr/bin/env python3
"""Render a report markdown file to HTML using the dashboard's design tokens.

  python3 render_md.py reports/CODE_REMEDIATION.md reports/remediation.html "Title"
"""

import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

EXTRA_CSS = """
.wrap{max-width:58rem;display:block;}
h1{font-size:clamp(1.8rem,4vw,2.6rem);margin:0 0 1rem;line-height:1.12;}
h2{margin:2.8rem 0 .5rem;padding-top:1.2rem;border-top:1px solid var(--rule);
  font-size:clamp(1.2rem,2.4vw,1.55rem);}
h3{font-size:1.02rem;margin:2rem 0 .6rem;font-weight:600;letter-spacing:-.005em;}
p{margin:0 0 1rem;}
ul{margin:0 0 1rem;padding-left:1.15rem;display:flex;flex-direction:column;gap:.45rem;
  max-width:68ch;}
li{color:var(--ink-2);}
hr{border:0;border-top:1px solid var(--rule);margin:2.4rem 0 0;}
hr + h2{border-top:0;padding-top:0;margin-top:1.6rem;}
pre.code{font-family:var(--mono);font-size:.78rem;line-height:1.6;background:var(--sunk);
  border:1px solid var(--rule-2);border-left:3px solid var(--accent);border-radius:2px;
  padding:.85rem 1rem;overflow-x:auto;margin:0 0 1rem;}
pre.code code{background:none;padding:0;font-size:1em;}
.tag{font-family:var(--mono);font-size:.58rem;letter-spacing:.11em;padding:.14rem .4rem;
  border-radius:2px;font-weight:600;vertical-align:.1em;white-space:nowrap;}
.tag--static{background:var(--bad-soft);color:var(--bad);}
.tag--sim{background:var(--warn-soft);color:var(--warn);}
.cmp td{vertical-align:top;font-family:var(--serif);font-size:.9rem;line-height:1.55;}
.cmp td:first-child{font-family:var(--mono);font-size:.76rem;color:var(--ink-3);
  white-space:nowrap;}
.cmp th{vertical-align:bottom;}
blockquote{margin:0 0 1rem;padding:.2rem 0 .2rem 1.1rem;border-left:3px solid var(--accent);
  color:var(--ink-2);}
"""


def _tokens():
    """Reuse the palette and type scale from the dashboard generator."""
    dash = open(os.path.join(HERE, "generate_dashboard.py")).read()
    return dash.split("    w('''\n", 1)[1].split("\n''')", 1)[0]


def _inline(t):
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
    t = t.replace("[STATIC]", '<span class="tag tag--static">STATIC</span>')
    t = t.replace("[SIM]", '<span class="tag tag--sim">SIM</span>')
    return t


def _is_block_start(line):
    s = line.lstrip()
    return (line.startswith("```") or line.startswith("|") or line.startswith("#")
            or s.startswith("- ") or line.strip() == "---" or not line.strip())


def render(md):
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)

    while i < n:
        start = i
        ln = lines[i]

        if not ln.strip():
            i += 1

        elif ln.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # consume closing fence
            out.append(f'<pre class="code"><code>{html.escape(chr(10).join(buf))}'
                       f"</code></pre>")

        elif ln.startswith("|"):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows
                     if set(r.replace("|", "").strip()) - set("- :")]
            if cells:
                t = ['<div class="mscroll"><table class="cmp"><thead><tr>']
                t += [f"<th>{_inline(c)}</th>" for c in cells[0]]
                t.append("</tr></thead><tbody>")
                for row in cells[1:]:
                    t.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row)
                             + "</tr>")
                t.append("</tbody></table></div>")
                out.append("".join(t))

        elif ln.strip() == "---":
            out.append("<hr>")
            i += 1

        elif ln.startswith("### "):
            out.append(f"<h3>{_inline(ln[4:])}</h3>")
            i += 1

        elif ln.startswith("## "):
            out.append(f"<h2>{_inline(ln[3:])}</h2>")
            i += 1

        elif ln.startswith("# "):
            out.append(f"<h1>{_inline(ln[2:])}</h1>")
            i += 1

        elif ln.lstrip().startswith("- "):
            items = []
            while i < n and lines[i].strip():
                cur = lines[i]
                if cur.lstrip().startswith("- "):
                    items.append(cur.lstrip()[2:])
                elif items and cur.startswith(" "):
                    items[-1] += " " + cur.strip()
                else:
                    break
                i += 1
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ul>")

        else:
            buf = []
            while i < n and lines[i].strip() and not _is_block_start(lines[i]):
                buf.append(lines[i].strip())
                i += 1
            if buf:
                out.append(f'<p>{_inline(" ".join(buf))}</p>')

        # Guarantee forward progress no matter which branch ran.
        if i <= start:
            i = start + 1

    return "\n".join(out)


def main():
    src, dest = sys.argv[1], sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else "Report"
    body = render(open(src).read())
    page = [f"<title>{html.escape(title)}</title>", "<style>", _tokens(), EXTRA_CSS,
            "</style>", '<div class="wrap">', body, "</div>"]
    with open(dest, "w") as fh:
        fh.write("\n".join(page) + "\n")
    print(f"wrote {dest} ({os.path.getsize(dest)} bytes)")


if __name__ == "__main__":
    main()
