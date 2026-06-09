#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
OUTPUT = ROOT / "index.html"


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
        lambda m: stash(
            f'<a href="{html.escape(normalize_href(m.group(2)), quote=True)}">{html.escape(m.group(1))}</a>'
        ),
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
    for path in sorted(CONTENT_DIR.glob("*.md")):
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
        f'<section id="{page["slug"]}" data-search data-source="{html.escape(page["path"])}">'
        f'<div class="source-note">Fonte editável: <code>{html.escape(page["path"])}</code></div>{page["html"]}</section>'
        for page in pages
    )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>POCUS UPA | Konted C10RL + My USG</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%2308756f'/%3E%3Ctext x='32' y='40' font-size='24' text-anchor='middle' fill='white' font-family='Arial' font-weight='700'%3EUS%3C/text%3E%3C/svg%3E">
  <style>
    :root {{
      --bg: #ffffff;
      --surface: #f7faf9;
      --surface-strong: #edf5f3;
      --ink: #102025;
      --muted: #52656c;
      --line: #d6e2e0;
      --accent: #08756f;
      --accent-dark: #064f4b;
      --accent-soft: #dff2ef;
      --warn: #b45309;
      --warn-soft: #fff3e0;
      --danger: #b91c1c;
      --danger-soft: #fee2e2;
      --ok: #15803d;
      --ok-soft: #e7f7ed;
      --max: 1120px;
      color-scheme: light;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--bg);
      line-height: 1.58;
    }}
    a {{ color: var(--accent); text-underline-offset: 3px; }}
    a:hover {{ color: var(--accent-dark); }}
    .layout {{
      display: grid;
      grid-template-columns: 260px minmax(0, 1fr);
      min-height: 100vh;
    }}
    aside {{
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      padding: 20px 16px;
      border-right: 1px solid var(--line);
      background: #fbfdfc;
    }}
    .brand {{
      border-bottom: 1px solid var(--line);
      padding-bottom: 16px;
      margin-bottom: 16px;
    }}
    .brand strong {{ display: block; font-size: 18px; }}
    .brand span {{ display: block; color: var(--muted); font-size: 13px; margin-top: 4px; }}
    nav a {{
      display: block;
      padding: 9px 10px;
      border-radius: 8px;
      color: var(--ink);
      text-decoration: none;
      font-size: 14px;
    }}
    nav a:hover {{ background: var(--accent-soft); color: var(--accent-dark); }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 4;
      border-bottom: 1px solid var(--line);
      background: rgba(255,255,255,.94);
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
    }}
    .actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .actions a, .actions button {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      padding: 10px 12px;
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      white-space: nowrap;
    }}
    main {{
      max-width: var(--max);
      margin: 0 auto;
      padding: 28px 22px 64px;
    }}
    section {{
      scroll-margin-top: 86px;
      border-bottom: 1px solid var(--line);
      padding: 34px 0;
    }}
    h1, h2, h3, h4, h5 {{ margin: 0 0 12px; line-height: 1.16; letter-spacing: 0; }}
    h1 {{ font-size: clamp(32px, 5vw, 52px); }}
    h2 {{ font-size: clamp(26px, 3.5vw, 38px); margin-top: 8px; }}
    h3 {{ font-size: 24px; margin-top: 28px; }}
    h4 {{ font-size: 19px; margin-top: 22px; }}
    p {{ margin: 0 0 12px; }}
    ul, ol {{ margin: 8px 0 16px; padding-left: 22px; }}
    li {{ margin: 6px 0; }}
    blockquote {{
      margin: 16px 0;
      padding: 12px 14px;
      border-left: 4px solid var(--accent);
      background: var(--surface);
      border-radius: 0 8px 8px 0;
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
    .source-note {{
      display: inline-block;
      margin-bottom: 14px;
      color: var(--muted);
      font-size: 12px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 9px;
    }}
    .figure {{
      margin: 18px 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 10px;
    }}
    .figure img {{ display: block; width: 100%; height: auto; }}
    .figure video {{ display: block; width: 100%; height: auto; border: 1px solid var(--line); border-radius: 8px; background: #000; }}
    figcaption {{ color: var(--muted); font-size: 13px; margin-top: 8px; }}
    .table-wrap {{ overflow-x: auto; margin: 14px 0 18px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border: 1px solid var(--line); padding: 10px; vertical-align: top; text-align: left; }}
    th {{ background: var(--surface-strong); }}
    .task input {{ margin-right: 8px; }}
    .hidden-by-search {{ display: none !important; }}
    @media (max-width: 900px) {{
      .layout {{ grid-template-columns: 1fr; }}
      aside {{ position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }}
      nav {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 4px; }}
      .topbar {{ position: static; }}
      .topbar-inner {{ flex-direction: column; align-items: stretch; }}
    }}
    @media print {{
      aside, .topbar, .source-note {{ display: none; }}
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
        <span>Fonte Markdown editável no Obsidian</span>
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
            <a href="content/00-inicio.md">Editar fonte</a>
            <a href="references/c10rl-3-in-1-color-doppler-ultrasound.pdf">PDF C10RL</a>
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
