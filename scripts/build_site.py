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
            f'<figure class="figure"><div class="figure-shell"><img loading="lazy" decoding="async" '
            f'src="{html.escape(normalize_href(m.group(2)), quote=True)}" '
            f'alt="{html.escape(m.group(1), quote=True)}"></div><figcaption>{html.escape(m.group(1))}</figcaption></figure>'
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
                '<div class="figure-shell">'
                f'<video controls preload="metadata" src="{html.escape(src, quote=True)}"{poster_attr}></video>'
                '</div>'
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


def render_hero_panel() -> str:
    return """
<aside class="hero-panel" aria-label="Resumo operacional do treinamento">
  <div class="hero-panel-inner">
    <p class="panel-kicker">Aparelho da aula</p>
    <figure class="hero-device">
      <img src="assets/media/componentes-c10rl-hero.jpg" width="860" height="645" loading="eager" decoding="async" alt="Diagrama técnico do aparelho Konted C10RL com bateria, módulo sem fio, botão de energia e transdutor">
    </figure>
    <div class="proof-grid" aria-label="Contexto do treinamento">
      <div><strong>Konted C10RL</strong><span>sonda sem fio</span></div>
      <div><strong>My USG</strong><span>app da prática</span></div>
      <div><strong>UPA</strong><span>uso à beira-leito</span></div>
      <div><strong>Central</strong><span>foco inicial</span></div>
    </div>
    <ol class="hero-steps" aria-label="Sequência mínima antes da prática">
      <li><span>01</span><strong>Ligar e conectar</strong><em>Wi-Fi da sonda, app correto, bateria.</em></li>
      <li><span>02</span><strong>Ajustar imagem</strong><em>profundidade, ganho, preset e marcador.</em></li>
      <li><span>03</span><strong>Fazer pré-scan</strong><em>veia, artéria, profundidade e limites.</em></li>
    </ol>
  </div>
</aside>"""


def build_html(pages: list[dict[str, str]]) -> str:
    nav = "\n".join(
        f'<a href="#{page["slug"]}" data-nav-target="{page["slug"]}"><span>{idx:02d}</span>{html.escape(page["title"])}</a>'
        for idx, page in enumerate(pages, start=1)
    )
    section_html = []
    for idx, page in enumerate(pages, start=1):
        body = page["html"]
        if idx == 1:
            marker = '<h3 id="h-o-que-e-pocus">'
            intro, rest = (body.split(marker, 1) + [""])[:2] if marker in body else (body, "")
            body = (
                '<div class="hero-grid">'
                f'<div class="hero-copy">{intro}</div>'
                f'{render_hero_panel()}'
                '</div>'
                f'<div class="section-rest">{marker if rest else ""}{rest}</div>'
            )
        section_html.append(
            f'<section id="{page["slug"]}" class="section-block reveal" data-search data-section="{idx:02d}">'
            f'{body}</section>'
        )
    sections = "\n".join(section_html)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Treinamento USG point-of-care | UPA</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23152123'/%3E%3Cpath d='M16 38c6 5 26 5 32 0' stroke='%23d79043' stroke-width='4' fill='none' stroke-linecap='round'/%3E%3Ctext x='32' y='31' font-size='19' text-anchor='middle' fill='%23f6f1e9' font-family='system-ui,sans-serif' font-weight='700'%3EUS%3C/text%3E%3C/svg%3E">
  <script>document.documentElement.classList.add('js');</script>
  <style>
    :root {{
      --bg: #f3f6f2;
      --paper: #fbfaf4;
      --surface: #fffdf7;
      --surface-quiet: #eef4ef;
      --surface-strong: #e2ece7;
      --ink: #152123;
      --ink-soft: #263636;
      --muted: #5f6c67;
      --rail: #101b1c;
      --rail-2: #172526;
      --rail-muted: #a9b7b1;
      --line: rgba(21, 33, 35, .14);
      --line-strong: rgba(21, 33, 35, .22);
      --accent: #126e68;
      --accent-dark: #0d514d;
      --accent-soft: #dfeee9;
      --amber: #b36b27;
      --amber-soft: #f6e4c9;
      --danger: #8f3c2e;
      --max: 1130px;
      --sidebar: 304px;
      --radius: 22px;
      --ease: cubic-bezier(.16, 1, .3, 1);
      --sans: "Plus Jakarta Sans", "Satoshi", "Geist", "Aptos", system-ui, sans-serif;
      --mono: "JetBrains Mono", "SFMono-Regular", ui-monospace, monospace;
      color-scheme: light;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      font-family: var(--sans);
      color: var(--ink);
      background: var(--bg);
      line-height: 1.62;
      text-rendering: optimizeLegibility;
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 5;
      opacity: .035;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160' viewBox='0 0 160 160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='.8'/%3E%3C/svg%3E");
    }}
    a {{ color: var(--accent); text-decoration-thickness: 1px; text-underline-offset: 4px; }}
    a:hover {{ color: var(--accent-dark); }}
    a:focus-visible, button:focus-visible, input:focus-visible {{
      outline: 3px solid rgba(179, 107, 39, .32);
      outline-offset: 3px;
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
      padding: 28px 18px;
      background: var(--rail);
      color: var(--rail-muted);
      box-shadow: inset -1px 0 0 rgba(246, 241, 233, .08);
    }}
    .brand {{
      position: relative;
      padding: 4px 8px 24px;
      margin-bottom: 16px;
      border-bottom: 1px solid rgba(246, 241, 233, .11);
    }}
    .brand::before {{
      content: "";
      display: block;
      width: 42px;
      height: 4px;
      border-radius: 999px;
      background: var(--amber);
      margin-bottom: 18px;
    }}
    .brand strong {{
      display: block;
      max-width: 9ch;
      color: #f6f1e9;
      font-size: 32px;
      font-weight: 760;
      letter-spacing: 0;
      line-height: .96;
    }}
    .brand span {{
      display: block;
      max-width: 22ch;
      color: var(--rail-muted);
      font-size: 13px;
      line-height: 1.45;
      margin-top: 12px;
    }}
    nav {{
      display: grid;
      gap: 3px;
    }}
    nav a {{
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr);
      align-items: center;
      min-height: 42px;
      gap: 10px;
      padding: 8px 10px 8px 6px;
      border-radius: 14px;
      color: #dbe5df;
      text-decoration: none;
      font-size: 14px;
      line-height: 1.24;
      transition: background-color .42s var(--ease), color .42s var(--ease), transform .42s var(--ease);
    }}
    nav a span {{
      font-family: var(--mono);
      color: var(--amber-soft);
      font-size: 11px;
      text-align: center;
      opacity: .8;
    }}
    nav a:hover {{
      background: rgba(246, 241, 233, .08);
      color: #fffdf7;
      transform: translateX(4px);
    }}
    nav a[aria-current="true"] {{
      background: rgba(246, 241, 233, .12);
      color: #fffdf7;
      box-shadow: inset 3px 0 0 var(--amber);
    }}
    nav a[aria-current="true"] span {{
      color: #fffdf7;
      opacity: 1;
    }}
    .topbar {{
      position: sticky;
      top: 18px;
      z-index: 4;
      max-width: calc(var(--max) + 56px);
      margin: 18px auto 0;
      padding: 7px;
      border-radius: 28px;
      background: rgba(251, 250, 244, .84);
      border: 1px solid rgba(21, 33, 35, .10);
      backdrop-filter: blur(16px);
      box-shadow: 0 24px 60px -44px rgba(15, 28, 29, .42), inset 0 1px 0 rgba(255, 253, 247, .74);
    }}
    .topbar-inner {{
      max-width: var(--max);
      margin: 0 auto;
      display: grid;
      grid-template-columns: minmax(260px, 1fr) auto;
      gap: 10px;
      align-items: center;
    }}
    input[type="search"] {{
      width: 100%;
      min-height: 46px;
      border: 0;
      border-radius: 22px;
      padding: 12px 16px;
      font: inherit;
      font-size: 15px;
      background: var(--surface);
      color: var(--ink);
      box-shadow: inset 0 0 0 1px rgba(21, 33, 35, .11);
    }}
    input[type="search"]::placeholder {{ color: #6f7c78; }}
    .actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    .actions a, .actions button {{
      min-height: 46px;
      border: 0;
      border-radius: 999px;
      background: var(--rail);
      color: #f6f1e9;
      padding: 12px 16px;
      font: inherit;
      font-size: 13px;
      font-weight: 760;
      text-decoration: none;
      cursor: pointer;
      white-space: nowrap;
      box-shadow: inset 0 1px 0 rgba(255, 253, 247, .10);
      transition: background-color .42s var(--ease), color .42s var(--ease), transform .42s var(--ease);
    }}
    .actions a:nth-child(2) {{ background: var(--accent-dark); }}
    .actions button {{ background: var(--amber); color: #20160d; }}
    .actions a:hover, .actions button:hover {{
      transform: translateY(-1px);
    }}
    .actions a:active, .actions button:active {{ transform: translateY(1px) scale(.99); }}
    main {{
      max-width: var(--max);
      margin: 0 auto;
      padding: 34px 30px 88px;
    }}
    .empty-state {{
      max-width: 760px;
      margin: 26px 0;
      padding: 18px 20px;
      border-radius: 20px;
      background: var(--surface);
      box-shadow: inset 0 0 0 1px var(--line);
      color: var(--muted);
    }}
    .section-block {{
      position: relative;
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr);
      column-gap: 34px;
      scroll-margin-top: 104px;
      border-bottom: 1px solid var(--line);
      padding: 70px 0;
    }}
    .section-block::before {{
      content: attr(data-section);
      grid-column: 1;
      grid-row: 1 / span 80;
      align-self: start;
      position: sticky;
      top: 112px;
      width: 56px;
      padding-top: 12px;
      border-top: 2px solid var(--amber);
      color: var(--amber);
      font-family: var(--mono);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: .08em;
    }}
    .section-block > * {{ grid-column: 2; }}
    .section-block:first-of-type {{
      grid-template-columns: minmax(0, 1fr);
      padding-top: 34px;
    }}
    .section-block:first-of-type::before {{ display: none; }}
    .section-block:first-of-type > * {{ grid-column: 1; }}
    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 380px;
      gap: 46px;
      align-items: start;
    }}
    .hero-copy {{
      min-width: 0;
    }}
    .section-rest {{
      margin-top: 44px;
    }}
    .hero-panel {{
      position: sticky;
      top: 108px;
      margin-top: 8px;
      padding: 7px;
      border-radius: 28px;
      background: rgba(16, 27, 28, .08);
      border: 1px solid rgba(21, 33, 35, .10);
      box-shadow: 0 30px 74px -56px rgba(15, 28, 29, .55), inset 0 1px 0 rgba(255, 253, 247, .84);
    }}
    .hero-panel-inner {{
      border-radius: 21px;
      padding: 20px;
      background: var(--rail);
      color: #f6f1e9;
      box-shadow: inset 0 1px 0 rgba(255, 253, 247, .10);
    }}
    .panel-kicker {{
      margin: 0 0 12px;
      color: var(--amber-soft);
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .10em;
      text-transform: uppercase;
    }}
    .hero-device {{
      display: grid;
      place-items: center;
      aspect-ratio: 4 / 3;
      margin: 0;
      overflow: hidden;
      border-radius: 16px;
      background: #f6f1e9;
    }}
    .hero-device img {{
      display: block;
      width: 100%;
      height: 100%;
      object-fit: contain;
    }}
    .proof-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      margin-top: 16px;
      border-top: 1px solid rgba(246, 241, 233, .14);
      border-left: 1px solid rgba(246, 241, 233, .14);
    }}
    .proof-grid > div {{
      padding: 12px 10px;
      border-right: 1px solid rgba(246, 241, 233, .14);
      border-bottom: 1px solid rgba(246, 241, 233, .14);
    }}
    .proof-grid strong {{
      display: block;
      color: #fffdf7;
      font-size: 13px;
      line-height: 1.2;
    }}
    .proof-grid span {{
      display: block;
      margin-top: 3px;
      color: var(--rail-muted);
      font-size: 12px;
      line-height: 1.3;
    }}
    .hero-steps {{
      list-style: none;
      margin: 16px 0 0;
      padding: 0;
      border-top: 1px solid rgba(246, 241, 233, .14);
    }}
    .hero-steps li {{
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr);
      gap: 10px;
      margin: 0;
      padding: 12px 0;
      border-bottom: 1px solid rgba(246, 241, 233, .14);
    }}
    .hero-steps li:last-child {{ border-bottom: 0; padding-bottom: 0; }}
    .hero-steps li > span {{
      color: var(--amber-soft);
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 700;
      line-height: 1.5;
    }}
    .hero-steps strong {{
      display: block;
      color: #fffdf7;
      font-size: 14px;
      line-height: 1.25;
    }}
    .hero-steps em {{
      display: block;
      margin-top: 3px;
      color: var(--rail-muted);
      font-size: 12px;
      font-style: normal;
      line-height: 1.4;
    }}
    h1, h2, h3, h4, h5 {{
      margin: 0 0 14px;
      line-height: 1.08;
      letter-spacing: 0;
      color: var(--ink);
    }}
    h2 {{
      max-width: 18ch;
      font-size: 38px;
      font-weight: 780;
    }}
    .section-block:first-of-type > h2:first-child {{
      max-width: 13ch;
      font-size: 52px;
      font-weight: 820;
      letter-spacing: 0;
    }}
    .section-block:first-of-type > h2:first-child::before {{
      content: "UPA / POCUS / Konted C10RL";
      display: block;
      width: max-content;
      max-width: 100%;
      margin-bottom: 18px;
      padding: 7px 10px;
      border-radius: 999px;
      background: var(--rail);
      color: var(--amber-soft);
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .10em;
    }}
    .section-block:first-of-type > p:first-of-type {{
      max-width: 760px;
      font-size: 19px;
      color: var(--ink-soft);
    }}
    h3 {{
      max-width: 24ch;
      margin-top: 40px;
      font-size: 25px;
      font-weight: 760;
    }}
    h3::before {{
      content: "";
      display: block;
      width: 30px;
      height: 3px;
      border-radius: 999px;
      background: var(--accent);
      margin-bottom: 12px;
    }}
    h4 {{
      margin-top: 26px;
      font-size: 19px;
      font-weight: 760;
    }}
    p {{
      margin: 0 0 13px;
      max-width: 74ch;
    }}
    ul, ol {{
      max-width: 74ch;
      margin: 10px 0 18px;
      padding-left: 24px;
    }}
    li {{ margin: 7px 0; }}
    blockquote {{
      max-width: 820px;
      margin: 22px 0;
      padding: 18px 20px;
      border-radius: 20px;
      background: var(--surface);
      box-shadow: inset 4px 0 0 var(--accent), inset 0 0 0 1px rgba(18, 110, 104, .16);
      color: var(--ink-soft);
      font-weight: 650;
    }}
    code {{
      background: var(--surface-strong);
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 2px 6px;
      font-size: .92em;
    }}
    pre code {{
      display: block;
      padding: 16px;
      overflow: auto;
    }}
    .figure {{
      width: min(100%, 700px);
      margin: 28px 0 20px;
      padding: 7px;
      border-radius: 24px;
      background: rgba(255, 253, 247, .74);
      border: 1px solid rgba(21, 33, 35, .10);
      box-shadow: 0 28px 70px -52px rgba(15, 28, 29, .48), inset 0 1px 0 rgba(255, 253, 247, .84);
    }}
    .figure-shell {{
      display: grid;
      place-items: center;
      min-height: 180px;
      overflow: hidden;
      border-radius: 17px;
      background: #182526;
      box-shadow: inset 0 1px 0 rgba(255, 253, 247, .12), inset 0 0 0 1px rgba(246, 241, 233, .08);
    }}
    .figure img {{
      display: block;
      width: 100%;
      height: auto;
      max-height: 380px;
      object-fit: contain;
      background: #182526;
    }}
    .video-figure {{ width: min(100%, 620px); }}
    .figure video {{
      display: block;
      width: 100%;
      height: auto;
      max-height: 420px;
      background: #182526;
    }}
    figcaption {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin: 9px 4px 1px;
    }}
    .table-wrap {{
      width: min(100%, 880px);
      overflow-x: auto;
      margin: 18px 0 24px;
      padding: 5px;
      border-radius: 20px;
      background: rgba(255, 253, 247, .78);
      border: 1px solid rgba(21, 33, 35, .10);
      box-shadow: 0 24px 62px -52px rgba(15, 28, 29, .38);
    }}
    table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      overflow: hidden;
      border-radius: 15px;
      font-size: 14px;
      background: var(--surface);
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      border-right: 1px solid var(--line);
      padding: 12px 13px;
      vertical-align: top;
      text-align: left;
    }}
    th:last-child, td:last-child {{ border-right: 0; }}
    tbody tr:last-child td {{ border-bottom: 0; }}
    th {{
      background: var(--surface-strong);
      color: var(--ink);
      font-weight: 760;
    }}
    tbody tr:nth-child(even) td {{ background: #f8faf5; }}
    .task input {{ margin-right: 8px; }}
    .hidden-by-search {{ display: none !important; }}
    .js .reveal, .js .figure, .js .table-wrap {{
      opacity: 0;
      transform: translateY(18px);
      transition: opacity .72s var(--ease), transform .72s var(--ease);
    }}
    .js .is-visible {{
      opacity: 1;
      transform: translateY(0);
    }}
    @media (max-width: 900px) {{
      .layout {{ grid-template-columns: 1fr; }}
      aside {{
        position: static;
        height: auto;
        padding: 22px 16px;
      }}
      .brand strong {{ max-width: none; font-size: 28px; }}
      .brand span {{ max-width: none; }}
      nav {{ grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 5px; }}
      nav a {{ min-height: 44px; }}
      .topbar {{
        position: static;
        margin: 14px 14px 0;
      }}
      .topbar-inner {{
        grid-template-columns: 1fr;
      }}
      .actions {{ justify-content: stretch; }}
      .actions a, .actions button {{ flex: 1 1 auto; text-align: center; }}
      main {{ padding: 24px 16px 62px; }}
      .section-block {{
        display: block;
        padding: 48px 0;
        scroll-margin-top: 18px;
      }}
      .section-block::before {{
        position: static;
        display: block;
        margin-bottom: 16px;
      }}
      .section-block:first-of-type {{ padding-top: 28px; }}
      .hero-grid {{ grid-template-columns: 1fr; gap: 24px; }}
      .hero-panel {{ position: static; max-width: 520px; }}
      .section-rest {{ margin-top: 34px; }}
      h2, .section-block:first-of-type > h2:first-child {{ font-size: 34px; max-width: 16ch; }}
      h3 {{ font-size: 22px; }}
      p, ul, ol {{ max-width: 100%; }}
      .figure {{ width: 100%; border-radius: 20px; }}
      .figure-shell {{ min-height: 140px; border-radius: 14px; }}
      .figure img {{ max-height: 310px; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
      *, *::before, *::after {{
        transition-duration: .01ms !important;
        animation-duration: .01ms !important;
        animation-iteration-count: 1 !important;
      }}
      .js .reveal, .js .figure, .js .table-wrap {{
        opacity: 1;
        transform: none;
      }}
    }}
    @media print {{
      body {{ background: #fffdf7; }}
      body::before, aside, .topbar {{ display: none; }}
      .layout {{ display: block; }}
      main {{ max-width: none; padding: 0; }}
      .section-block {{ display: block; padding: 24px 0; page-break-inside: avoid; }}
      .section-block::before {{ display: none; }}
      .figure, .table-wrap {{ box-shadow: none; }}
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
        <p id="emptyState" class="empty-state" hidden>Nenhuma seção encontrada para essa busca. Tente termos como conexão, acesso, ganho, limpeza ou FOAM.</p>
        {sections}
      </main>
    </div>
  </div>
  <script>
    const searchInput = document.getElementById('searchInput');
    const emptyState = document.getElementById('emptyState');
    const sections = Array.from(document.querySelectorAll('[data-search]'));
    const applySearch = () => {{
      const term = searchInput.value.trim().toLowerCase();
      let visibleCount = 0;
      sections.forEach((section) => {{
        const text = section.innerText.toLowerCase();
        const hidden = term.length > 1 && !text.includes(term);
        section.classList.toggle('hidden-by-search', hidden);
        if (!hidden) visibleCount += 1;
      }});
      emptyState.hidden = term.length <= 1 || visibleCount > 0;
    }};
    searchInput.addEventListener('input', applySearch);
    document.querySelectorAll('a[href^="#"]').forEach((link) => {{
      link.addEventListener('click', () => {{
        searchInput.value = '';
        sections.forEach((section) => section.classList.remove('hidden-by-search'));
        emptyState.hidden = true;
      }});
    }});
    const navLinks = Array.from(document.querySelectorAll('[data-nav-target]'));
    const navBySection = new Map(navLinks.map((link) => [link.dataset.navTarget, link]));
    const setActiveSection = (sectionId) => {{
      navLinks.forEach((link) => link.removeAttribute('aria-current'));
      const activeLink = navBySection.get(sectionId);
      if (activeLink) activeLink.setAttribute('aria-current', 'true');
    }};
    setActiveSection(sections[0]?.id);
    const revealTargets = Array.from(document.querySelectorAll('.reveal, .figure, .table-wrap'));
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduceMotion && 'IntersectionObserver' in window) {{
      const observer = new IntersectionObserver((entries) => {{
        entries.forEach((entry) => {{
          if (entry.isIntersecting) {{
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }}
        }});
      }}, {{ threshold: 0.08, rootMargin: '0px 0px -8% 0px' }});
      revealTargets.forEach((target, index) => {{
        target.style.transitionDelay = `${{Math.min(index * 18, 140)}}ms`;
        observer.observe(target);
      }});
    }} else {{
      revealTargets.forEach((target) => target.classList.add('is-visible'));
    }}
    if ('IntersectionObserver' in window) {{
      const navObserver = new IntersectionObserver((entries) => {{
        entries.forEach((entry) => {{
          if (entry.isIntersecting) setActiveSection(entry.target.id);
        }});
      }}, {{ rootMargin: '-34% 0px -55% 0px', threshold: 0.01 }});
      sections.forEach((section) => navObserver.observe(section));
    }}
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
