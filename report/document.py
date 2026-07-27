"""One document model, two renderers (per toolkit D-029, lab D-024).

Markdown and standalone HTML render from the same block structure, so
the two formats cannot drift apart in content. The HTML embeds its own
CSS and fetches nothing; the stylesheet deliberately contains no percent
signs so the bare-rate scanner applies to the whole rendered byte stream
(the JE lab's scanner once flagged its own `width: 100%` — the CSS
changed, not the scanner). Both renderers run the language and rate
guards before returning: a document that cannot pass does not exist.
"""

from html import escape

from report.guard import check_document_text, check_offline

# --- block constructors ---------------------------------------------------


def p(text):
    return ("p", text)


def note(text):
    return ("note", text)


def kv(pairs):
    return ("kv", list(pairs))


def table(headers, rows):
    return ("table", list(headers), [list(r) for r in rows])


def bullets(items):
    return ("list", list(items))


def section(heading, *blocks):
    return {"heading": heading, "blocks": list(blocks)}


def doc(title, subtitle, *sections):
    return {"title": title, "subtitle": subtitle, "sections": list(sections)}


# --- markdown renderer ----------------------------------------------------


def _md_block(block, out):
    kind = block[0]
    if kind == "p":
        out.append(block[1])
    elif kind == "note":
        out.append("> " + block[1])
    elif kind == "kv":
        for k, v in block[1]:
            out.append("- **{0}:** {1}".format(k, v))
    elif kind == "list":
        for item in block[1]:
            out.append("- " + str(item))
    elif kind == "table":
        headers, rows = block[1], block[2]
        out.append("| " + " | ".join(str(h) for h in headers) + " |")
        out.append("|" + "|".join(" --- " for _ in headers) + "|")
        for row in rows:
            out.append("| " + " | ".join(
                str(c).replace("|", "\\|").replace("\n", " ")
                for c in row) + " |")
    else:
        raise ValueError("unknown block kind: " + kind)
    out.append("")


def render_markdown(document):
    out = ["# " + document["title"], "", document["subtitle"], ""]
    for sec in document["sections"]:
        out.append("## " + sec["heading"])
        out.append("")
        for block in sec["blocks"]:
            _md_block(block, out)
    text = "\n".join(out).rstrip() + "\n"
    check_document_text(text)
    return text


# --- standalone HTML renderer ---------------------------------------------

_CSS = """
body { font-family: Georgia, 'Times New Roman', serif; margin: 2rem auto;
       max-width: 60rem; color: rgb(25, 30, 35); line-height: 1.45; }
h1 { font-size: 1.6rem; border-bottom: 2px solid rgb(25, 30, 35);
     padding-bottom: 0.4rem; }
h2 { font-size: 1.15rem; margin-top: 1.6rem; }
p.subtitle { color: rgb(90, 96, 102); font-style: italic; }
table { border-collapse: collapse; margin: 0.6rem 0; }
th, td { border: 1px solid rgb(170, 175, 180); padding: 0.3rem 0.55rem;
         text-align: left; vertical-align: top; font-size: 0.92rem; }
th { background: rgb(238, 240, 242); }
blockquote { border-left: 4px solid rgb(170, 175, 180); margin: 0.6rem 0;
             padding: 0.2rem 0.8rem; color: rgb(90, 96, 102); }
dl { margin: 0.4rem 0; }
dt { font-weight: bold; }
dd { margin: 0 0 0.35rem 1.2rem; }
"""


def _html_block(block, out):
    kind = block[0]
    if kind == "p":
        out.append("<p>{0}</p>".format(escape(block[1])))
    elif kind == "note":
        out.append("<blockquote>{0}</blockquote>".format(escape(block[1])))
    elif kind == "kv":
        out.append("<dl>")
        for k, v in block[1]:
            out.append("<dt>{0}</dt><dd>{1}</dd>".format(
                escape(str(k)), escape(str(v))))
        out.append("</dl>")
    elif kind == "list":
        out.append("<ul>")
        for item in block[1]:
            out.append("<li>{0}</li>".format(escape(str(item))))
        out.append("</ul>")
    elif kind == "table":
        headers, rows = block[1], block[2]
        out.append("<table><thead><tr>")
        for h in headers:
            out.append("<th>{0}</th>".format(escape(str(h))))
        out.append("</tr></thead><tbody>")
        for row in rows:
            out.append("<tr>" + "".join(
                "<td>{0}</td>".format(escape(str(c))) for c in row) + "</tr>")
        out.append("</tbody></table>")
    else:
        raise ValueError("unknown block kind: " + kind)


def render_html(document):
    out = ["<!DOCTYPE html>", "<html><head><meta charset=\"utf-8\">",
           "<title>{0}</title>".format(escape(document["title"])),
           "<style>{0}</style>".format(_CSS), "</head><body>",
           "<h1>{0}</h1>".format(escape(document["title"])),
           "<p class=\"subtitle\">{0}</p>".format(
               escape(document["subtitle"]))]
    for sec in document["sections"]:
        out.append("<h2>{0}</h2>".format(escape(sec["heading"])))
        for block in sec["blocks"]:
            _html_block(block, out)
    out.append("</body></html>")
    text = "\n".join(out) + "\n"
    check_document_text(text)
    check_offline(text)
    return text


def write_document(document, path_base):
    """Write .md and .html renderings; returns the two paths."""
    md_path = path_base + ".md"
    html_path = path_base + ".html"
    with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_markdown(document))
    with open(html_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_html(document))
    return md_path, html_path
