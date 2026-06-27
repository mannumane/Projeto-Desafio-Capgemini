# Exemplos de Perguntas e Respostas — Persona "Ana"

> Respostas **reais** geradas pela Ana com o banco conectado (Gemini + tool calling).
> Cada resposta vem de uma consulta executada no banco, registrada como evidência.

---

### 1. Clientes mais valiosos

**Pergunta:** "Quem são meus clientes mais valiosos e quanto representam da receita?"

**Ana:**
> Os clientes mais valiosos são os do segmento "Campeões", que representam 193 clientes e geram 40,12% da receita total (R$ 921.597,37). Considerando a alta representatividade na receita, focar em estratégias de retenção e programas de fidelidade para esses clientes tende a trazer o maior retorno.
> *Fonte: KPI rfm_resumo.*

**Evidência (consulta executada):** `query_database` → `SELECT * FROM v_rfm_resumo` (6 linhas)

---

### 2. Saúde da política de descontos

**Pergunta:** "A política de desconto está saudável?"

**Ana:**
> A política de descontos não está totalmente saudável. Embora descontos de até 20% ainda gerem lucro (R$ 100.785,47 para a faixa de 1–20%), as faixas acima de 20% estão resultando em prejuízo:
> - Descontos entre 21–40% geraram prejuízo total de R$ 35.817,47.
> - Descontos entre 41–60% resultaram em prejuízo de R$ 28.944,19.
> - Descontos acima de 60% foram os mais prejudiciais, com prejuízo de R$ 70.614,40.
>
> **Ação priorizada:** revisão urgente da política de descontos para faixas acima de 20%, pois impactam negativamente a lucratividade. É crucial entender se esses descontos são estratégicos (girar estoque, atrair clientes) e se o retorno justifica o prejuízo.
> *Fonte: KPI desconto_lucro.*

**Evidência (consulta executada):** `query_database` → `SELECT * FROM v_desconto_lucro` (5 linhas)

---

### 3. Pergunta sem dado disponível (fallback honesto)

**Pergunta:** "Qual a margem de lucro por fornecedor?"

**Ana:**
> Com os dados disponíveis, não é possível concluir a margem de lucro por fornecedor, pois não temos informações sobre fornecedores em nosso banco de dados. No entanto, posso te informar a margem de lucro por categoria de produto, que pode ajudar a entender a rentabilidade de diferentes grupos de produtos. Se desejar, posso buscar essa informação.

**Evidência (consulta executada):** `get_schema` → inspecionou os 14 objetos do banco e concluiu que não há tabela/coluna de fornecedor.

> Este exemplo é o mais importante para a avaliação: mostra que a IA **não alucina**. Quando o dado não existe, ela admite e oferece a análise mais próxima.

---

## Por que estas respostas atendem ao requisito crítico

O desafio exige que toda resposta da IA esteja **baseada nos dados conectados, com evidência, e sem ser genérica**. Em cada exemplo acima:

1. A Ana **executou uma consulta real** no banco antes de responder (coluna "Evidência").
2. Citou **números reais** (R$ 921.597,37; R$ 100.785,47; etc.) e a **fonte** (qual KPI).
3. No caso 3, **reconheceu o limite dos dados** em vez de inventar.

E como a Ana usa as mesmas views que alimentam o Power BI (`get_kpi`), os números que ela fala são **idênticos aos do dashboard** quando aplicado o mesmo recorte de filtros.

---

## Outras perguntas para testar na demonstração
- "Quais categorias dão mais lucro?"
- "Qual estado tem a maior receita?"
- "Compare o ticket médio dos segmentos Campeões e Perdidos."
- "Quanto os Campeões representam só na região Oeste?" (mostra coerência com o dashboard filtrado)
- "Qual o produto mais vendido em quantidade?"
