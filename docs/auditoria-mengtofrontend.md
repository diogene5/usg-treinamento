# Auditoria MengToFrontend

Repositório usado: `https://github.com/Kappaemme-git/MengToFrontend`

Skill instalada em:

```text
/Users/diogenes/.codex/skills/mengtofrontend
```

## Diagnóstico do site antes da revisão

Launch readiness: needs polish.

Top fixes:

1. Primeira dobra pouco específica: o texto falava de USG/POCUS, mas o aparelho e o app da aula não apareciam como prova visual imediata.
2. Hierarquia visual melhorou no ajuste anterior, mas ainda faltava um ponto de entrada operacional que conectasse aparelho, conexão e prática.
3. Navegação sem estado ativo: o menu ajudava a pular seções, mas não mostrava onde o leitor estava.

## Ajustes aplicados

- Texto inicial reescrito para citar **Konted C10RL** e **My USG** logo na primeira frase.
- Primeira dobra ganhou um painel operacional com imagem técnica pequena do C10RL, sem substituir o conteúdo clínico.
- A imagem do hero usa uma cópia otimizada (`assets/media/componentes-c10rl-hero.jpg`) para não carregar o PNG original de alta resolução na primeira dobra.
- O painel mostra sequência mínima de plantão: ligar/conectar, ajustar imagem e fazer pré-scan.
- Menu lateral ganhou estado ativo por `IntersectionObserver`, sem `scroll` contínuo.
- As imagens principais continuam limitadas em tamanho para não dominar a leitura.

## Checklist MengToFrontend

- Typography and letter spacing: pass. Sem tracking negativo; hierarquia por escala, peso e espaço.
- Real references and imagery: pass parcial. Site usa imagem local do C10RL e imagens reais do SAEM para acesso central.
- Image refinement: pass parcial. Imagens não geradas para anatomia/procedimento; hero usa imagem técnica local pequena.
- Prompt/design specificity: pass. Linguagem e interface agora citam UPA, Konted C10RL, My USG, acesso central e pré-scan.
- Human touch and micro-interactions: pass. Estado ativo do menu, busca com estado vazio e revelação leve respeitando `prefers-reduced-motion`.
- Mobile visual quality: precisa validação visual contínua após cada mudança de conteúdo.

## Risco residual

O site ainda depende de revisão humana para aprovar definitivamente qualquer imagem local do aparelho. Se a imagem técnica do C10RL incomodar ou parecer artificial, a melhor substituição é uma foto real do aparelho na UPA.
