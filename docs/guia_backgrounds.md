# Guia — Aplicar os backgrounds no Power BI

3 imagens prontas em `dashboard/backgrounds/` (2560×1440, proporção 16:9 do Power BI, paleta Capgemini):
- `bg_pagina1_executiva.png`
- `bg_pagina2_clientes.png`
- `bg_pagina3_produtos.png`

## Como aplicar (por página)

1. No Power BI, garanta o canvas em **16:9** (padrão). Em **View → Page view → Fit to page**.
2. Clique numa área vazia da página. No painel **Format** (Formatar) → **Canvas background**:
   - **Image → Browse** → selecione o PNG da página.
   - **Image fit: Fit**
   - **Transparency: 0%**
3. Repita para cada uma das 3 páginas com o PNG correspondente.

## Como posicionar os visuais em cima

Para cada visual que você inserir:
- **Desligue o título do visual** (Format → Title → Off) — o card do fundo já tem o título.
- **Deixe o fundo do visual transparente** (Format → Effects → Background → Off, ou Transparency 100%).
- Posicione o visual **dentro da área branca do card**, logo abaixo da faixa de título.

Para alinhar com precisão, selecione o visual e em **Format → General → Properties → Size and position** digite os valores (o canvas é 1280×720; as coordenadas abaixo já consideram a faixa de título de ~44px):

### Página 1 — Visão Executiva
| Visual | X | Y | Largura | Altura |
|---|---|---|---|---|
| Card "Receita Total" | 30 | 120 | 221 | 52 |
| Card "Lucro Total" | 279 | 120 | 221 | 52 |
| Card "Margem %" | 528 | 120 | 221 | 52 |
| Card "Ticket Médio" | 777 | 120 | 221 | 52 |
| Card "Nº Pedidos" | 1026 | 120 | 221 | 52 |
| Linha – Tendência | 34 | 240 | 740 | 226 |
| Mapa – Estado | 810 | 240 | 436 | 226 |
| Barras – Categoria | 34 | 536 | 1212 | 150 |
| Slicers (Ano/Região/Categoria) | 846 / 986 / 1126 | 16 | 128 | 30 |

### Página 2 — Clientes (RFM)
| Visual | X | Y | Largura | Altura |
|---|---|---|---|---|
| Card "% Receita Campeões" | 30 | 120 | 388 | 52 |
| Card "Clientes Campeões" | 446 | 120 | 388 | 52 |
| Card "Total de Clientes" | 862 | 120 | 388 | 52 |
| Barras – Segmento RFM | 34 | 240 | 588 | 446 |
| Tabela – Top 10 Clientes | 658 | 240 | 588 | 188 |
| Dispersão – Valor×Freq. | 658 | 498 | 588 | 188 |

### Página 3 — Produtos & Descontos
| Visual | X | Y | Largura | Altura |
|---|---|---|---|---|
| Barras – Top 10 Produtos | 34 | 128 | 588 | 462 |
| Treemap – Cat/Subcat | 658 | 128 | 588 | 196 |
| Dispersão – Desconto×Lucro | 658 | 394 | 588 | 196 |
| (a faixa "INSIGHT" já vem escrita no fundo — não precisa de visual) | | | | |

> Dica: depois de posicionar tudo, em **View → Lock objects** trava o layout para não desalinhar.

## Observação
Os textos cinza-claro dentro dos cards ("[ valor ]", "barras: ...") são apenas dicas de posicionamento e ficam **cobertos** pelos visuais. Se algum cantinho aparecer, é só ajustar o tamanho do visual.
