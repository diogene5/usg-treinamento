# Como editar e publicar

Este material foi montado para ser editado no Obsidian e publicado como site estático.

## Editar

1. Abra `/Users/diogenes/vaults/usg_treinamento` no Obsidian.
2. Edite as páginas em `content/`.
3. Guarde imagens novas em `assets/media/`, mas só inclua no site público depois de aprovação explícita.
4. Guarde PDFs/fontes locais em `references/`.
5. Rode `python3 scripts/build_site.py`.
6. Abra `index.html`.

## Publicar

Para publicar em GitHub Pages, Netlify, Vercel, Cloudflare Pages ou hospedagem estática, envie:

- `index.html`
- `content/`
- `assets/`
- `references/`
- `docs/`
- `README.md`

## Atualização rápida

No macOS, você pode dar duplo clique em `atualizar-site.command`.

## Privacidade

Os screenshots `IMG_6455.png` e `IMG_6456.png` ficam preservados na raiz do vault como evidência local, mas não entram no site porque contêm conversa privada. O conteúdo técnico deles foi convertido em texto.

As imagens, vídeos e diagramas didáticos ficam preservados como material de apoio. A versão pública atual usa texto, tabelas, checklists e links externos para evitar publicar mídia ainda não aprovada.
