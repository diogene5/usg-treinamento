#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
OUTPUT = ROOT / "index.html"
SITE_TITLE = "Treinamento POCUS UPA"
SITE_DESCRIPTION = (
    "Trilha de aprendizado de POCUS para médicos e enfermeiros da UPA: "
    "cuidados com o Konted C10RL, conexão My USG, primeira imagem útil, "
    "acesso central supervisionado, checklists e fontes FOAM."
)
UPDATED_AT = "10/06/2026"
WIFI_PASSWORD = "uxccgdh397"
APP_PASSWORD = "123456"
MANUAL_OFFICIAL = "references/c10rl-pro-myusg-quick-user-manual-v1-1.pdf"

@dataclass(frozen=True)
class ModuleSpec:
    file: str
    slug: str
    title: str
    description: str
    time: str
    badge: str = ""
    badge_kind: str = ""
    wide: bool = False
    open_by_default: bool = False

@dataclass(frozen=True)
class StageSpec:
    slug: str
    number: str
    kicker: str
    title: str
    lede: str
    tint: str
    modules: tuple[ModuleSpec, ...]

STAGES: tuple[StageSpec, ...] = (
    StageSpec(
        slug="etapa-1",
        number="01",
        kicker="Etapa 1 · antes da aula · ~10 min",
        title="Chegue com o app no bolso e as regras na cabeça",
        lede="O início é deliberadamente simples: entender o uso focado do POCUS, instalar o My USG e memorizar as regras que evitam falsa segurança.",
        tint="",
        modules=(
            ModuleSpec("00-inicio.md", "mod-inicio", "O que é POCUS — e o que não é", "Ultrassom à beira-leito com pergunta clínica limitada e imediata. A fronteira do método é parte da segurança.", "leitura · 4 min"),
            ModuleSpec("01-baixar-app.md", "mod-app", "Baixar o app My USG", "Instale antes da aula para sobrar tempo de prática: iPhone por Wi-Fi; Android por Wi-Fi ou cabo compatível.", "2 min + download"),
        ),
    ),
    StageSpec(
        slug="etapa-2",
        number="02",
        kicker="Etapa 2 · operar o aparelho · ~30 min",
        title="Ligue, conecte e gere imagem sem travar",
        lede="A parte que destrava todo o resto: ordem de conexão, senha certa, controles básicos, limpeza e troubleshooting de plantão.",
        tint="stage--alt",
        modules=(
            ModuleSpec("02-conexao-my-usg.md", "mod-conexao", "Conexão My USG", "Sempre na mesma ordem: ligar a sonda, entrar no Wi-Fi dela, abrir o app. O erro número 1 é confundir as senhas.", "leitura · 10 min", "duas senhas", "core"),
            ModuleSpec("03-cuidados-limpeza.md", "mod-cuidados", "Cuidados e limpeza", "Conferir antes, proteger durante, limpar depois. O aparelho precisa continuar funcionando para toda a equipe.", "leitura · 6 min"),
            ModuleSpec("04-controles-imagem.md", "mod-controles", "Controles de imagem", "Não procure uma imagem perfeita: procure uma imagem útil. Profundidade, ganho, preset, marcador e freeze/live.", "leitura · 10 min"),
        ),
    ),
    StageSpec(
        slug="etapa-3",
        number="03",
        kicker="Etapa 3 · na prática · ~90 min",
        title="Mão na sonda: a sequência da primeira prática",
        lede="A competência mínima é operacional. Acesso central é o núcleo supervisionado; pulmão, eFAST e eco básico entram como demonstrações, não como obrigação inicial.",
        tint="stage--tint",
        modules=(
            ModuleSpec("05-o-que-vamos-treinar.md", "mod-treinar", "O que vamos treinar", "A primeira prática é uma sequência repetível: conectar, gerar imagem, ajustar, salvar, limpar e verbalizar limitações.", "leitura · 8 min"),
            ModuleSpec("07-acesso-vascular.md", "mod-acesso-central", "Acesso central guiado por ultrassom", "Pré-scan, veia vs. artéria, jugular interna, profundidade e regra da ponta. Procedimento real exige supervisão direta.", "20 min + prática", "núcleo obrigatório", "core", True),
            ModuleSpec("05-protocolos-pocus.md", "mod-protocolos", "Pulmão, eFAST e eco básico", "Protocolos demonstrativos para reconhecer perguntas úteis e limites do método. Não são competência mínima da primeira aula.", "demonstração · 15 min", "demonstração", "demo"),
        ),
    ),
    StageSpec(
        slug="etapa-4",
        number="04",
        kicker="Etapa 4 · depois da aula · consulta contínua",
        title="Fixe o que importa e saiba onde estudar",
        lede="Referência pós-aula: armadilhas, checklist de plantão e fontes FOAM. Use no celular quando o aparelho ou a imagem não colaborarem.",
        tint="stage--alt",
        modules=(
            ModuleSpec("06-armadilhas.md", "mod-armadilhas", "Armadilhas e falsas seguranças", "Situações em que o exame engana quem está começando: conexão, imagem, protocolos e procedimentos.", "revisão · 10 min", "revisão", "demo", True),
            ModuleSpec("09-checklists.md", "mod-checklists", "Checklists rápidos", "Antes da aula, conexão, limpeza pós-uso e entrega mínima do aluno. Feito para consulta no plantão.", "consulta rápida", "uso no plantão", "core", True),
            ModuleSpec("08-fontes-foam.md", "mod-fontes", "Fontes para estudar depois", "Links abertos para revisar depois da aula: vídeos, atlas, podcasts e manuais.", "consulta contínua"),
        ),
    ),
)

PUBLIC_FILES = [module.file for stage in STAGES for module in stage.modules]


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
        return "#mod-fontes" if "fontes" in href.lower() else href
    return href


def render_link(label: str, href: str) -> str:
    escaped_href = html.escape(normalize_href(href), quote=True)
    escaped_label = html.escape(label)
    attrs = ""
    if escaped_href.startswith(("http://", "https://")):
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
            '<figure class="figure"><div class="figure-shell"><img loading="lazy" decoding="async" '
            f'src="{html.escape(normalize_href(m.group(2)), quote=True)}" '
            f'alt="{html.escape(m.group(1), quote=True)}"></div><figcaption>{html.escape(m.group(1))}</figcaption></figure>'
        ),
        text,
    )
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: stash(render_link(m.group(1), m.group(2))), text)
    text = re.sub(r"`([^`]+)`", lambda m: stash(f"<code>{html.escape(m.group(1))}</code>"), text)
    rendered = html.escape(text)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", rendered)
    for idx, value in enumerate(tokens):
        rendered = rendered.replace(f"\u0000{idx}\u0000", value)
    return rendered


def render_table(lines: list[str]) -> str:
    rows = [[inline(cell.strip()) for cell in line.strip().strip("|").split("|")] for line in lines]
    header = rows[0]
    body = rows[2:]
    out = ['<div class="table-scroll"><div class="table-wrap"><table><thead><tr>']
    out.extend(f"<th>{cell}</th>" for cell in header)
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        out.extend(f"<td>{cell}</td>" for cell in row)
        out.append("</tr>")
    out.append("</tbody></table></div></div>")
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
            close_list(); i += 1; continue
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
                '<figure class="figure video-figure"><div class="figure-shell">'
                f'<video controls preload="metadata" src="{html.escape(src, quote=True)}"{poster_attr}></video>'
                f'</div><figcaption>{html.escape(caption)}</figcaption></figure>'
            )
            i += 1
            continue
        if re.match(r"^!\[[^\]]*\]\([^)]+\)$", stripped):
            close_list(); out.append(inline(stripped)); i += 1; continue
        if stripped.startswith(">"):
            close_list(); out.append(f'<blockquote>{inline(stripped.lstrip("> ").strip())}</blockquote>'); i += 1; continue
        unordered = re.match(r"^[-*]\s+(.+)$", stripped)
        if unordered:
            if list_type != "ul":
                close_list(); out.append("<ul>"); list_type = "ul"
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
                close_list(); out.append("<ol>"); list_type = "ol"
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


def strip_first_heading(rendered: str) -> str:
    return re.sub(r"^\s*<h2[^>]*>.*?</h2>\s*", "", rendered, count=1, flags=re.S)


def read_pages() -> dict[str, dict[str, str]]:
    pages: dict[str, dict[str, str]] = {}
    for filename in PUBLIC_FILES:
        path = CONTENT_DIR / filename
        if not path.exists():
            raise SystemExit(f"Pagina publica nao encontrada: {path}")
        text = path.read_text(encoding="utf-8")
        first_heading = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
        title = first_heading.group(1).strip() if first_heading else path.stem
        pages[filename] = {"title": title, "path": str(path.relative_to(ROOT)), "html": render_markdown(text)}
    return pages


def wave() -> str:
    return '''<div class="wave-sep" aria-hidden="true"><svg viewBox="0 0 1200 36" preserveAspectRatio="none" focusable="false"><path d="M0 18 q 15 -14 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></div>'''


def badge_html(module: ModuleSpec) -> str:
    if not module.badge:
        return ""
    cls = "badge badge--core" if module.badge_kind == "core" else "badge"
    return f'<span class="{cls}">{html.escape(module.badge)}</span>'


def render_module(module: ModuleSpec, idx: int, total: int, pages: dict[str, dict[str, str]]) -> str:
    page = pages[module.file]
    body = strip_first_heading(page["html"])
    all_modules = [m for s in STAGES for m in s.modules]
    if idx < total:
        next_mod = all_modules[idx]
        next_link = f'<a class="next-link" href="#{next_mod.slug}">Próximo: {html.escape(next_mod.title)} →</a>'
    else:
        next_link = '<a class="next-link" href="#topo">Voltar ao topo ↑</a>'
    open_attr = " open" if module.open_by_default else ""
    wide_attr = " module--wide" if module.wide else ""
    return f'''
        <details class="module{wide_attr}" id="{module.slug}" data-module data-stage-module{open_attr}>
          <summary>
            <span class="module-expand" aria-hidden="true">+</span>
            <span class="module-top"><span class="module-no">Módulo {idx:02d}</span>{badge_html(module)}<span class="chip">{html.escape(module.time)}</span></span>
            <h3 class="module-title">{html.escape(module.title)}</h3>
            <span class="module-desc">{html.escape(module.description)}</span>
            <span class="done-chip">concluído</span>
          </summary>
          <div class="module-body">
            {body}
            <div class="module-foot">
              <button type="button" class="complete-btn" data-complete="{module.slug}" aria-pressed="false"><span class="cb-box" aria-hidden="true"></span><span class="cb-label">Marcar como concluído</span></button>
              {next_link}
              <span class="source-path">{html.escape(page['path'])}</span>
            </div>
          </div>
        </details>'''


def render_stage(stage: StageSpec, start_idx: int, total: int, pages: dict[str, dict[str, str]]) -> str:
    modules_html = []
    for offset, module in enumerate(stage.modules):
        modules_html.append(render_module(module, start_idx + offset, total, pages))
    tint = f" {stage.tint}" if stage.tint else ""
    return f'''
  <section class="stage{tint}" id="{stage.slug}" aria-labelledby="t-{stage.slug}">
    <div class="stage-inner">
      <header class="stage-head">
        <span class="stage-num" aria-hidden="true">{stage.number}</span>
        <p class="stage-kicker">{html.escape(stage.kicker)}</p>
        <h2 id="t-{stage.slug}">{html.escape(stage.title)}</h2>
        <p class="stage-lede">{html.escape(stage.lede)}</p>
        <p class="stage-progress"><span data-stage-count>0/{len(stage.modules)}</span> módulos concluídos</p>
      </header>
      <div class="modules">
        {''.join(modules_html)}
      </div>
    </div>
  </section>'''


def render_topbar(total: int) -> str:
    nav = "".join(
        f'<a href="#{stage.slug}"><b>{stage.number}</b>{html.escape(stage.kicker.split("·")[1].strip())}</a>'
        for stage in STAGES
    )
    mnav_groups: list[str] = []
    idx = 1
    for stage in STAGES:
        items = []
        for module in stage.modules:
            items.append(
                f'<li><a href="#{module.slug}" data-mnav="{module.slug}">'
                f'<span class="mnav-no">{idx:02d}</span>'
                f'<span class="mnav-name">{html.escape(module.title)}</span>'
                f'<span class="mnav-done" aria-hidden="true">✓</span></a></li>'
            )
            idx += 1
        short = stage.kicker.split("·")[1].strip() if "·" in stage.kicker else stage.title
        mnav_groups.append(
            f'<section class="mnav-group">'
            f'<a class="mnav-stage" href="#{stage.slug}"><b>{stage.number}</b>{html.escape(short)}'
            f'<small>{html.escape(stage.kicker.split("·")[-1].strip())}</small></a>'
            f'<ul>{"".join(items)}</ul></section>'
        )
    return f'''
<header class="topbar">
  <div class="topbar-inner">
    <a class="wordmark" href="#topo">POCUS<b>·</b>UPA <small>trilha</small></a>
    <nav class="stage-nav" aria-label="Etapas da trilha">{nav}</nav>
    <div class="search-wrap" role="search">
      <button type="button" class="icon-btn search-toggle" id="search-toggle" aria-expanded="false" aria-controls="search-bar" aria-label="Buscar nos módulos">
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </button>
      <div class="search-bar" id="search-bar">
        <div class="search-field">
          <svg class="search-ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <input id="search-input" type="search" placeholder="Buscar nos módulos…" aria-label="Buscar nos módulos" autocomplete="off">
          <button type="button" class="search-clear" id="search-clear" aria-label="Limpar busca" hidden>✕</button>
        </div>
        <p class="search-count" id="search-count" aria-live="polite" hidden></p>
      </div>
    </div>
    <button type="button" class="icon-btn theme-toggle" id="theme-toggle" aria-label="Tema: automático (tocar para mudar)">
      <span class="tt tt-auto" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor"/></svg></span>
      <span class="tt tt-light" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><circle cx="12" cy="12" r="4.4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4M5.4 5.4l1.7 1.7M16.9 16.9l1.7 1.7M18.6 5.4l-1.7 1.7M7.1 16.9l-1.7 1.7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></span>
      <span class="tt tt-dark" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 1 0 11 11z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg></span>
    </button>
    <a class="plantao-btn" id="plantao-btn" href="#plantao">
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M13 2 4.5 13.5H10L9 22l8.5-11.5H12L13 2z" fill="currentColor"/></svg>
      Plantão
    </a>
    <div class="trail-progress" aria-live="polite">
      <span class="tp-label" id="progress-label">0/{total} módulos</span>
      <div class="tp-bar" aria-hidden="true"><i id="progress-fill"></i></div>
    </div>
    <details class="mnav" id="mnav">
      <summary aria-label="Abrir menu de etapas e módulos">
        <span class="mnav-ico" aria-hidden="true"><i></i><i></i><i></i></span>
        <span class="sr-only">Menu</span>
      </summary>
      <nav class="mnav-panel" aria-label="Etapas e módulos da trilha">
        <p class="mnav-progress"><span id="mnav-progress-label">0/{total} módulos concluídos</span></p>
        {"".join(mnav_groups)}
      </nav>
    </details>
  </div>
</header>'''


def render_plantao_dialog() -> str:
    wifi = html.escape(WIFI_PASSWORD)
    app = html.escape(APP_PASSWORD)
    manual = html.escape(MANUAL_OFFICIAL, quote=True)
    return f'''
<dialog class="plantao" id="plantao" aria-labelledby="plantao-title">
  <header class="plantao-head">
    <p class="plantao-kicker">Acesso rápido · consulta de plantão</p>
    <h2 id="plantao-title">Modo plantão</h2>
    <button type="button" class="plantao-close" aria-label="Fechar painel do plantão">✕</button>
  </header>
  <div class="plantao-body">
    <section aria-labelledby="p-t-senhas">
      <h3 id="p-t-senhas">As duas senhas</h3>
      <div class="creds">
        <div class="cred">
          <span class="cred-which">1 · Wi-Fi da sonda (iPhone, iPad, Android)</span>
          <strong class="cred-value">{wifi}</strong>
          <span class="cred-note">Senha desta sonda da UPA. Digite em <strong>minúsculas</strong>, sem espaços. Em outras unidades, o fabricante usa o número de série (SN) gravado na carcaça — nesta sonda, o valor é <strong>{wifi}</strong>.</span>
          <button type="button" class="copy-btn" data-copy="{wifi}" aria-label="Copiar senha do Wi-Fi ({wifi})"><span class="copy-label">copiar senha</span></button>
          <span class="sr-only" aria-live="polite" data-copy-status></span>
        </div>
        <div class="cred">
          <span class="cred-which">2 · App My USG · usuário Administer</span>
          <strong class="cred-value">{app}</strong>
          <span class="cred-note">Senha inicial do app, no perfil <strong>Administer</strong>. Se fizer sentido para o plantão, ative o Auto login.</span>
          <button type="button" class="copy-btn" data-copy="{app}" aria-label="Copiar a senha do app ({app})"><span class="copy-label">copiar senha</span></button>
          <span class="sr-only" aria-live="polite" data-copy-status></span>
        </div>
      </div>
    </section>
    <section aria-labelledby="p-t-manual">
      <h3 id="p-t-manual">Manual oficial</h3>
      <p><a class="btn btn--ghost" href="{manual}" target="_blank" rel="noopener">Abrir manual C10RL Pro + My USG (PDF)</a></p>
      <p class="small-note">PDF local — funciona offline após o primeiro acesso. Outros manuais no módulo <a href="#mod-fontes">Fontes FOAM</a>.</p>
    </section>
    <section aria-labelledby="p-t-90s">
      <h3 id="p-t-90s">Sequência de recuperação em 90 segundos</h3>
      <ol class="count90">
        <li>A sonda está ligada?</li>
        <li>A bateria da sonda está suficiente?</li>
        <li>O celular está conectado ao Wi-Fi <strong>da sonda</strong>, não ao Wi-Fi da UPA?</li>
        <li>A senha digitada foi <strong>{wifi}</strong> (minúsculas, sem espaços)?</li>
        <li>O My USG foi aberto <strong>depois</strong> da conexão Wi-Fi?</li>
        <li>Há outro celular/tablet conectado à sonda?</li>
        <li>O app volta a funcionar se fechar e abrir?</li>
        <li>A imagem aparece se pressionar o botão físico freeze/live?</li>
      </ol>
      <p class="small-note">Se falhar depois disso: pare e troque de dispositivo. O passo a passo completo está no módulo <a href="#mod-conexao">Conexão My USG</a>.</p>
    </section>
    <section aria-label="Avisos de segurança">
      <div class="plantao-stop" role="note">
        <b>SE A PONTA DA AGULHA SUMIU, PARE.</b>
        <span>Não avance o instrumento sem ver a ponta. Reencontre a ponta antes de avançar; sem confirmação, peça ajuda e não prossiga.</span>
      </div>
      <div class="callout callout--warn plantao-confuse"><strong>Não confundir:</strong> senha do Wi-Fi da sonda (<code>{wifi}</code>) ≠ senha do app My USG (<code>{app}</code>).</div>
    </section>
    <section class="plantao-links" aria-label="Atalhos">
      <a class="btn" href="#mod-checklists">Abrir os checklists de plantão</a>
    </section>
  </div>
</dialog>'''


def render_footer() -> str:
    return f'''
<footer>
  <svg class="foot-wave" viewBox="0 0 1200 36" preserveAspectRatio="none" aria-hidden="true" focusable="false">
    <path d="M0 18 q 15 -14 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>
  <div class="foot-inner">
    <div class="foot-grid">
      <div>
        <h3>Escopo deste material</h3>
        <p>Trilha educacional interna para o treinamento de POCUS da equipe da UPA (Konted C10RL + app My USG). Não substitui protocolos institucionais, manuais do fabricante nem julgamento clínico. Procedimentos reais exigem supervisão direta e protocolo local.</p>
      </div>
      <div>
        <h3>Como editar</h3>
        <p>O conteúdo vive em arquivos Markdown (<code>content/*.md</code>) no vault Obsidian do projeto. Edite os arquivos e rode <code>python3 scripts/build_site.py</code> ou <code>atualizar-site.command</code> para regenerar e publicar no GitHub Pages.</p>
      </div>
      <div>
        <h3>Créditos de imagem</h3>
        <p>Imagens do módulo de acesso central: <a href="https://www.saem.org/about-saem/academies-interest-groups-affiliates2/cdem/for-students/online-education/m3-curriculum/bedside-ultrasonagraphy/venous-access" target="_blank" rel="noopener">SAEM, “Venous access”</a> — cortesia de Sierra Beck, MD, e Bradley Wallace, MD. Usadas com atribuição, para fins educacionais.</p>
      </div>
    </div>
  </div>
  <div class="foot-meta">
    <span>Material atualizado em {UPDATED_AT} · uso educacional · conteúdo não substitui julgamento clínico · V3.1 trilha + plantão</span>
    <a href="#topo">Voltar ao topo ↑</a>
  </div>
</footer>'''


def render_hero() -> str:
    stage_cards = "".join(
        f'<li><a href="#{stage.slug}"><span class="hs-num">{stage.number}</span><span class="hs-name">{html.escape(stage.title.split(":")[0])}</span><span class="hs-time">{len(stage.modules)} módulos</span></a></li>'
        for stage in STAGES
    )
    return f'''
  <section class="hero" id="topo" aria-label="Apresentação da trilha">
    <div class="hero-text">
      <p class="eyebrow">UPA · Konted C10RL · app My USG</p>
      <h1>Do aparelho na caixa à <em>primeira imagem útil</em>.</h1>
      <p class="lede">Trilha de aprendizado de ultrassom point-of-care para médicos e enfermeiros <strong>sem contato prévio</strong> com ultrassom: ligar, conectar, gerar uma imagem básica, reconhecer limitações e pedir ajuda cedo.</p>
      <p class="hero-note">O aparelho é da equipe. Quem trabalha na UPA precisa saber conectar, cuidar e usar com responsabilidade. O objetivo não é formar especialista: é não travar na frente do paciente.</p>
      <div class="hero-actions"><a class="btn" href="#etapa-1">Começar a etapa 1</a><a class="btn btn--ghost" href="#mod-checklists">Checklists de plantão</a></div>
      <ul class="hero-stages">{stage_cards}</ul>
    </div>
    <figure class="hero-figure">
      <img src="assets/media/componentes-c10rl-hero.jpg" alt="Componentes do aparelho Konted C10RL: sonda sem fio de duas faces, cabo de carregamento e acessórios" width="800" height="770">
      <figcaption>Konted C10RL — sonda sem fio com face convexa e linear</figcaption>
    </figure>
  </section>'''


def render_html(pages: dict[str, dict[str, str]]) -> str:
    all_modules = [module for stage in STAGES for module in stage.modules]
    total = len(all_modules)
    stage_html = []
    idx = 1
    for stage in STAGES:
        stage_html.append(render_stage(stage, idx, total, pages))
        idx += len(stage.modules)
        stage_html.append(wave())
    stages = "\n".join(stage_html[:-1])
    return f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{SITE_TITLE}</title>
<meta name="description" content="{html.escape(SITE_DESCRIPTION, quote=True)}">
<meta name="theme-color" content="#faf7f1" id="meta-theme">
<link rel="stylesheet" href="assets/site.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23faf7f1'/%3E%3Crect x='1.5' y='1.5' width='61' height='61' rx='12.5' fill='none' stroke='%230f6e66' stroke-width='3'/%3E%3Cpath d='M10 38 q 5.5 -13 11 0 t 11 0 t 11 0 t 11 0' stroke='%230f6e66' stroke-width='4' fill='none' stroke-linecap='round'/%3E%3Ccircle cx='32' cy='18' r='4.5' fill='%23c98a3d'/%3E%3C/svg%3E">
<script>document.documentElement.classList.add('js');</script>
<script>(function(){{try{{var s=localStorage.getItem('pocusV31.theme');var t=(s==='light'||s==='dark'||s==='auto')?s:'auto';document.documentElement.setAttribute('data-theme',t);}}catch(e){{document.documentElement.setAttribute('data-theme','auto')}}}})();</script>
</head>
<body>
<a class="skip" href="#conteudo">Pular para o conteúdo</a>
{render_topbar(total)}
<main id="conteudo" tabindex="-1">
  {render_hero()}
  {wave()}
  {stages}
</main>
{render_plantao_dialog()}
{render_footer()}
<script src="assets/site.js"></script>
</body>
</html>
'''


def main() -> None:
    pages = read_pages()
    OUTPUT.write_text(render_html(pages), encoding="utf-8")
    print(f"Site atualizado: {OUTPUT}")
    print(f"Paginas fonte: {len(pages)}")

if __name__ == "__main__":
    main()
