# Roteiro de Apresentação — Desafio Data + Analytics + IA

> Apresentação ao vivo, ~8–10 min. Fala em primeira pessoa, conectando **tecnologia → decisão de negócio** (é o que a banca valoriza).

---

## Antes de começar (checklist técnico)
- [ ] App web já **acordado** (abra o link 5 min antes e mande 1 pergunta).
- [ ] Power BI aberto na **Visão Executiva**, com filtros limpos.
- [ ] Bot do Telegram rodando (`python app/telegram_bot.py`) e conversa **limpa** (Clear History).
- [ ] `.env` com a chave e modelo certos; internet ok.
- [ ] Slides (Canva) abertos.

---

## Slide 1 — Capa
*"Esse projeto transforma dados de vendas em decisões, com uma camada de IA conectada aos dados reais. Vou mostrar do dado bruto até uma analista de IA que responde perguntas de negócio com evidência."*

## Slide 2 — Problema e Objetivo
- *"O problema: uma empresa de varejo tem dados, mas precisa transformá-los em decisão — e explorar IA de forma aplicada, não genérica."*
- *"A solução responde perguntas reais: quem são os clientes mais valiosos, quais produtos/categorias dão mais lucro, se a política de desconto é saudável, onde estão as oportunidades por região."*
- Mensagem-chave: **comecei pelo negócio, não pela tecnologia.**

## Slide 3 — Arquitetura
- *"O princípio central é uma fonte única de verdade: um banco que alimenta tanto o dashboard quanto a IA. Assim os dois sempre falam os mesmos números."*
- Fluxo: CSV → ETL (Python) → banco SQLite (tabelas + views de KPI) → Power BI **e** IA.
- *"Decisão de arquitetura: dashboard e IA leem o MESMO banco. É isso que garante coerência."*

## Slide 4 — Camada de Dados e Indicadores
- *"Dataset Superstore, ~10 mil pedidos. Um ETL idempotente limpa, modela em esquema estrela e calcula os indicadores."*
- Números: receita US$ 2,29 mi · margem 12,5% · ticket médio US$ 459.
- Destaque: **os Campeões (RFM) são ~24% dos clientes e geram ~40% da receita.** E **descontos acima de 20% dão prejuízo médio.**
- Mensagem-chave: **indicadores que viram decisão**, não números soltos.

## Slide 5 — Dashboard Power BI  (DEMO 1)
- Trocar para o Power BI. Mostrar as 3 páginas rapidamente.
- *"Conectado ao banco via ODBC — não é Excel nem estático. Tem filtros, drill-down, e atualiza com um Refresh sem reconstruir nada."*
- Mostrar 1 filtro (ex: região) mexendo nos números.

## Slide 6 — Camada de IA: a Ana  (DEMO 2 — o ponto alto)
- *"A Ana é uma analista de BI sintética. A regra de ouro dela: nunca responde um número sem consultar o banco."*
- **Demo no app web:**
  1. Pergunte: *"Quem são meus clientes mais valiosos e quanto representam?"* → mostra a resposta com número + evidência (abrir "Ver evidência" e mostrar o SQL).
  2. **Prova de coerência:** mostre que o número da Ana bate com o do Power BI.
  3. Ligue o **RAG** e pergunte sobre desconto → ela combina o dado + a política do documento.
  4. Pergunte algo **sem dado** (ex: "margem por fornecedor?") → ela responde honestamente que não dá. **Esse é o momento mais importante: a IA não alucina.**
- **Demo no Telegram (wow):** mande a mesma pergunta no Telegram → *"o núcleo é desacoplado do canal; a mesma IA roda no web e no Telegram, e poderia ir pro WhatsApp, Slack, onde o cliente estiver."*

## Slide 7 — Decisões, Limitações e Próximos Passos
- Trade-offs: *"Usei tool calling (e não só RAG) porque os dados são estruturados; o número vem de uma consulta real, então não tem como inventar. SQLite pela simplicidade do desafio."*
- Coerência: IA e dashboard usam as mesmas views.
- Limitações (honestidade = senioridade): base sem custo por fornecedor; dataset histórico; SQLite não é produção.
- Próximos passos: deploy já feito (link público), automação do ETL, RAG sobre mais documentos.
- Fechamento: *"Uma solução coerente, funcional, explicável e conectada a dados reais."*

---

## Perguntas que a banca pode fazer (e como responder)

**"O dashboard é dinâmico ou estático?"**
Dinâmico. Conectado ao banco por ODBC; mudou o dado, um Refresh atualiza tudo sem reconstruir. A IA é ainda mais direta: consulta o banco a cada pergunta, então reflete na hora.

**"Como a IA garante que não inventa?"**
Tool calling: o modelo gera um SQL, eu executo no banco e ele responde com o resultado real. O app mostra o SQL como evidência. E se o dado não existe, ela diz que não é possível concluir.

**"Por que tool calling e não RAG?"**
Os dados são estruturados (números em tabelas). Tool calling/SQL brilha com isso. RAG eu uso como camada extra, para documentos de regra de negócio — mostro as duas técnicas.

**"E se o número da IA divergir do dashboard?"**
Os dois leem as mesmas views de KPI, então batem — desde que o mesmo recorte de filtro seja aplicado. (Bom citar que filtro diferente = contexto diferente, não erro.)

**"Isso escala / vai para produção?"**
O desafio não pedia produção. Mas o desenho permite: trocar SQLite por Postgres, ETL como job agendado, IA atrás de uma API. A arquitetura já é desacoplada.

---

## Mensagens para repetir ao longo da fala
- "Fonte única de verdade: dashboard e IA falam os mesmos números."
- "A IA responde com evidência — número + a consulta que o gerou."
- "Quando não há dado, ela admite. Não alucina."
- "O núcleo é desacoplado do canal."
