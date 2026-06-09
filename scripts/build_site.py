#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
OUTPUT = ROOT / "index.html"

# Only these pages are published to the team-facing site. Other Markdown files
# stay in the vault as internal support material for preparing the training.
PUBLIC_PAGES = [
    "00-inicio.md",
    "01-baixar-app.md",
    "02-conexao-my-usg.md",
    "03-cuidados-limpeza.md",
    "04-controles-imagem.md",
    "05-o-que-vamos-treinar.md",
    "05-protocolos-pocus.md",
    "07-acesso-vascular.md",
    "06-armadilhas.md",
    "08-roteiro-aula.md",
    "09-checklists.md",
    "08-fontes-foam.md",
]


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "secao"


def normalize_href(href: str) -> str:
    href = href.strip()
    if href.startswith("../"):
        href = href[3:]
    if href.endswith(".md") and not href.startswith(("http://", "https://")):
        return "#fontes" if "fontes" in href.lower() else href
    return href


def render_link(label: str, href: str) -> str:
    escaped_href = html.escape(href, quote=True)
    escaped_label = html.escape(label)
    attrs = ""
    if href.startswith(("http://", "https://")):
        attrs = ' target="_blank" rel="noopener"'
    return f'<a href="{escaped_href}"{attrs}>{escaped_label}</a>'


def inline(text: str) -> str:
    tokens: list[str] = []

    def stash(value: str) -> str:
        tokens.append(value)
        return f"\u0000{len(tokens) - 1}\u0000"

    text = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda m: stash(
            f'<figure class="figure"><img src="{html.escape(normalize_href(m.group(2)), quote=True)}" '
            f'alt="{html.escape(m.group(1), quote=True)}"><figcaption>{html.escape(m.group(1))}</figcaption></figure>'
        ),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: stash(render_link(m.group(1), normalize_href(m.group(2)))),
        text,
    )
    text = re.sub(r"`([^`]+)`", lambda m: stash(f"<code>{html.escape(m.group(1))}</code>"), text)

    rendered = html.escape(text)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)

    for idx, value in enumerate(tokens):
        rendered = rendered.replace(f"\u0000{idx}\u0000", value)
    return rendered


def render_table(lines: list[str]) -> str:
    rows = []
    for line in lines:
        cells = [inline(cell.strip()) for cell in line.strip().strip("|").split("|")]
        rows.append(cells)

    header = rows[0]
    body = rows[2:]
    out = ['<div class="table-wrap"><table><thead><tr>']
    out.extend(f"<th>{cell}</th>" for cell in header)
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        out.extend(f"<td>{cell}</td>" for cell in row)
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    i = 0
    list_type: str | None = None
    in_code = False
    code_lines: list[str] = []

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                close_list()
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not stripped:
            close_list()
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            close_list()
            table_lines = [stripped, lines[i + 1].strip()]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            out.append(render_table(table_lines))
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            close_list()
            level = min(len(heading.group(1)) + 1, 5)
            text = heading.group(2).strip()
            out.append(f'<h{level} id="h-{slugify(text)}">{inline(text)}</h{level}>')
            i += 1
            continue

        video = re.match(r"^\{\{video:([^|}]+)(?:\|([^|}]*))?(?:\|([^|}]*))?\}\}$", stripped)
        if video:
            close_list()
            src = normalize_href(video.group(1))
            caption = video.group(2).strip() if video.group(2) else "Vídeo"
            poster = normalize_href(video.group(3)) if video.group(3) else ""
            poster_attr = f' poster="{html.escape(poster, quote=True)}"' if poster else ""
            out.append(
                '<figure class="figure video-figure">'
                f'<video controls preload="metadata" src="{html.escape(src, quote=True)}"{poster_attr}></video>'
                f'<figcaption>{html.escape(caption)}</figcaption></figure>'
            )
            i += 1
            continue

        if re.match(r"^!\[[^\]]*\]\([^)]+\)$", stripped):
            close_list()
            out.append(inline(stripped))
            i += 1
            continue

        if stripped.startswith(">"):
            close_list()
            out.append(f'<blockquote>{inline(stripped.lstrip("> ").strip())}</blockquote>')
            i += 1
            continue

        unordered = re.match(r"^[-*]\s+(.+)$", stripped)
        if unordered:
            if list_type != "ul":
                close_list()
                out.append("<ul>")
                list_type = "ul"
            item = unordered.group(1)
            checked = re.match(r"^\[( |x|X)\]\s+(.+)$", item)
            if checked:
                state = " checked" if checked.group(1).lower() == "x" else ""
                out.append(f'<li class="task"><input type="checkbox"{state} disabled> {inline(checked.group(2))}</li>')
            else:
                out.append(f"<li>{inline(item)}</li>")
            i += 1
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered:
            if list_type != "ol":
                close_list()
                out.append("<ol>")
                list_type = "ol"
            out.append(f"<li>{inline(ordered.group(1))}</li>")
            i += 1
            continue

        close_list()
        out.append(f"<p>{inline(stripped)}</p>")
        i += 1

    close_list()
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(out)


def read_pages() -> list[dict[str, str]]:
    pages = []
    for filename in PUBLIC_PAGES:
        path = CONTENT_DIR / filename
        if not path.exists():
            raise SystemExit(f"Pagina publica nao encontrada: {path}")
        text = path.read_text(encoding="utf-8")
        first_heading = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
        title = first_heading.group(1).strip() if first_heading else path.stem
        pages.append(
            {
                "title": title,
                "slug": slugify(title),
                "path": str(path.relative_to(ROOT)),
                "html": render_markdown(text),
            }
        )
    return pages


def build_html(pages: list[dict[str, str]]) -> str:
    nav = "\n".join(f'<a href="#{page["slug"]}">{html.escape(page["title"])}</a>' for page in pages)
    sections = "\n".join(
        f'<section id="{page["slug"]}" data-search>'
        f'{page["html"]}</section>'
        for page in pages
    )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Treinamento USG point-of-care | UPA</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%2308756f'/%3E%3Ctext x='32' y='40' font-size='24' text-anchor='middle' fill='white' font-family='Arial' font-weight='700'%3EUS%3C/text%3E%3C/svg%3E">
  <style>
    :root {{
      --bg: #fbfcfc;
      --surface: #ffffff;
      --surface-quiet: #f4f7f6;
      --surface-strong: #e8efed;
      --ink: #172326;
      --muted: #5b686b;
      --line: #d8e1df;
      --accent: #08756f;
      --accent-dark: #064f4b;
      --accent-soft: #dff2ef;
      --amber: #8a5a12;
      --amber-soft: #fff6e6;
      --max: 1160px;
      --sidebar: 282px;
      color-scheme: light;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: var(--ink);
      background: var(--bg);
      line-height: 1.58;
      text-rendering: optimizeLegibility;
    }}
    a {{ color: var(--accent); text-decoration-thickness: 1px; text-underline-offset: 3px; }}
    a:hover {{ color: var(--accent-dark); }}
    a:focus-visible, button:focus-visible, input:focus-visible {{
      outline: 3px solid rgba(8,117,111,.24);
      outline-offset: 2px;
    }}
    .layout {{
      display: grid;
      grid-template-columns: var(--sidebar) minmax(0, 1fr);
      min-height: 100dvh;
    }}
    aside {{
      position: sticky;
      top: 0;
      height: 100dvh;
      overflow: auto;
      padding: 22px 16px;
      border-right: 1px solid var(--line);
      background: #f6faf9;
    }}
    .brand {{
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
      margin-bottom: 14px;
    }}
    .brand strong {{ display: block; font-size: 20px; line-height: 1.12; }}
    .brand span {{ display: block; color: var(--muted); font-size: 13px; margin-top: 6px; }}
    nav a {{
      display: block;
      padding: 8px 10px;
      border-radius: 8px;
      color: var(--ink);
      text-decoration: none;
      font-size: 14px;
      line-height: 1.28;
      transition: background-color .18s ease, color .18s ease, transform .18s ease;
    }}
    nav a:hover {{ background: var(--accent-soft); color: var(--accent-dark); transform: translateX(2px); }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 4;
      border-bottom: 1px solid var(--line);
      background: rgba(251,252,252,.94);
      backdrop-filter: blur(12px);
      padding: 14px 22px;
    }}
    .topbar-inner {{
      max-width: var(--max);
      margin: 0 auto;
      display: flex;
      gap: 12px;
      align-items: center;
    }}
    input[type="search"] {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 11px 12px;
      font-size: 15px;
      background: var(--surface);
      color: var(--ink);
    }}
    .actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .actions a, .actions button {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      color: var(--ink);
      padding: 10px 12px;
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      white-space: nowrap;
      transition: border-color .18s ease, color .18s ease, transform .18s ease;
    }}
    .actions a:hover, .actions button:hover {{ border-color: var(--accent); color: var(--accent-dark); }}
    .actions a:active, .actions button:active {{ transform: translateY(1px); }}
    main {{
      max-width: var(--max);
      margin: 0 auto;
      padding: 26px 26px 72px;
    }}
    section {{
      scroll-margin-top: 86px;
      border-bottom: 1px solid var(--line);
      padding: 38px 0;
    }}
    section:first-of-type {{
      padding-top: 26px;
    }}
    section:first-of-type h1 {{
      max-width: 920px;
      font-size: 48px;
      letter-spacing: 0;
    }}
    section:first-of-type > p:first-of-type {{
      max-width: 760px;
      font-size: 18px;
      color: var(--muted);
    }}
    h1, h2, h3, h4, h5 {{ margin: 0 0 12px; line-height: 1.16; letter-spacing: 0; }}
    h1 {{ font-size: 42px; }}
    h2 {{ font-size: 32px; margin-top: 8px; }}
    h3 {{ font-size: 24px; margin-top: 28px; }}
    h4 {{ font-size: 19px; margin-top: 22px; }}
    p {{ margin: 0 0 12px; max-width: 78ch; }}
    ul, ol {{ margin: 8px 0 16px; padding-left: 22px; }}
    li {{ margin: 6px 0; }}
    blockquote {{
      margin: 16px 0;
      padding: 14px 16px;
      border-left: 4px solid var(--accent);
      background: var(--surface-quiet);
      border-radius: 0 8px 8px 0;
      max-width: 84ch;
    }}
    code {{
      background: var(--surface-strong);
      border: 1px solid var(--line);
      border-radius: 5px;
      padding: 1px 5px;
      font-size: .92em;
    }}
    pre code {{
      display: block;
      padding: 14px;
      overflow: auto;
    }}
    .figure {{
      margin: 18px 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 10px;
    }}
    .figure img {{ display: block; width: 100%; height: auto; }}
    .figure video {{ display: block; width: 100%; height: auto; border: 1px solid var(--line); border-radius: 8px; background: #12181a; }}
    figcaption {{ color: var(--muted); font-size: 13px; margin-top: 8px; }}
    .table-wrap {{ overflow-x: auto; margin: 14px 0 18px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; background: var(--surface); }}
    th, td {{ border: 1px solid var(--line); padding: 11px 12px; vertical-align: top; text-align: left; }}
    th {{ background: var(--surface-strong); color: #263638; }}
    tbody tr:nth-child(even) td {{ background: #fafcfc; }}
    .task input {{ margin-right: 8px; }}
    .hidden-by-search {{ display: none !important; }}
    @media (max-width: 900px) {{
      .layout {{ grid-template-columns: 1fr; }}
      aside {{ position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }}
      nav {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 4px; }}
      .topbar {{ position: static; }}
      .topbar-inner {{ flex-direction: column; align-items: stretch; }}
      main {{ padding: 22px 16px 56px; }}
      section {{ padding: 30px 0; scroll-margin-top: 18px; }}
      h1, section:first-of-type h1 {{ font-size: 34px; }}
      h2 {{ font-size: 27px; }}
      h3 {{ font-size: 22px; }}
    }}
    @media print {{
      aside, .topbar {{ display: none; }}
      .layout {{ display: block; }}
      main {{ max-width: none; padding: 0; }}
      section {{ page-break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <aside>
      <div class="brand">
        <strong>POCUS UPA</strong>
        <span>Guia rápido para uso na UPA</span>
      </div>
      <nav aria-label="Navegação">
        {nav}
      </nav>
    </aside>
    <div>
      <header class="topbar">
        <div class="topbar-inner">
          <input id="searchInput" type="search" placeholder="Buscar no material: conexão, ganho, pneumotórax, acesso...">
          <div class="actions">
            <a href="https://apps.apple.com/br/app/my-usg/id1606311898" target="_blank" rel="noopener">App Store</a>
            <a href="https://play.google.com/store/apps/details?id=com.konted.wirelesskus" target="_blank" rel="noopener">Google Play</a>
            <button type="button" onclick="window.print()">Imprimir</button>
          </div>
        </div>
      </header>
      <main>
        {sections}
      </main>
    </div>
  </div>
  <script>
    const searchInput = document.getElementById('searchInput');
    const sections = Array.from(document.querySelectorAll('[data-search]'));
    searchInput.addEventListener('input', () => {{
      const term = searchInput.value.trim().toLowerCase();
      sections.forEach((section) => {{
        const text = section.innerText.toLowerCase();
        section.classList.toggle('hidden-by-search', term.length > 1 && !text.includes(term));
      }});
    }});
    document.querySelectorAll('a[href^="#"]').forEach((link) => {{
      link.addEventListener('click', () => {{
        searchInput.value = '';
        sections.forEach((section) => section.classList.remove('hidden-by-search'));
      }});
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    pages = read_pages()
    if not pages:
        raise SystemExit("Nenhum arquivo Markdown encontrado em content/.")
    OUTPUT.write_text(build_html(pages), encoding="utf-8")
    print(f"Site atualizado: {OUTPUT}")
    print(f"Paginas fonte: {len(pages)}")


if __name__ == "__main__":
    main()
