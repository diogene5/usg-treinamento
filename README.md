# Treinamento POCUS na UPA

Vault editável e site estático para treinamento inicial de médicos e enfermeiros sem contato prévio com ultrassom point of care, usando o **USG Konted C10RL** e o app **My USG**.

Este projeto agora está no diretório correto:

```bash
/Users/diogenes/vaults/usg_treinamento
```

## Como usar

1. Abra esta pasta no Obsidian como vault.
2. Edite as páginas em [content/](content).
3. Para atualizar o site, dê duplo clique em [atualizar-site.command](atualizar-site.command) ou rode:

```bash
python3 scripts/build_site.py
```

4. Abra [index.html](index.html) no navegador.

## Estrutura

- [content/](content): páginas principais do site, pensadas para edição no Obsidian.
- [docs/](docs): roteiro, checklists, armadilhas, fontes e evidências dos arquivos originais.
- [assets/media/](assets/media): imagens e vídeo didáticos com nomes limpos.
- [assets/diagrams/](assets/diagrams): diagramas SVG usados no site.
- [references/](references): cópias dos PDFs originais do aparelho e do app.
- [index.html](index.html): site estático gerado.

## Arquivos originais preservados

Os arquivos que você colocou originalmente na raiz do vault foram preservados. As cópias usadas pelo site ficam em `assets/media/` e `references/` para facilitar publicação e organização.

## Observações clínicas e operacionais

- O material é educacional e deve ser aplicado com supervisão, política institucional e protocolos locais.
- A parte de conexão e troubleshooting usa os manuais locais do My USG/Konted e os prints/vídeo enviados como evidência operacional.
- Os screenshots de conversa não foram publicados no site por conterem conversa privada; os pontos úteis foram convertidos em instruções textuais.
- O conector Raindrop não está disponível neste ambiente. A lista de fontes externas foi montada por busca web e pode receber depois links exportados do seu Raindrop.
