# Conteúdo para os slides (copiar/colar no Canva)

> Os diagramas estão em `apresentacao/arquitetura_solucao.png` e `apresentacao/arquitetura_ia.png`.
> No Canva: **Uploads → enviar a imagem → arrastar para o slide**.

---

## Slide 3 — Arquitetura da Solução
**Imagem:** `arquitetura_solucao.png` (ocupando a maior parte do slide).

**Legenda / fala:** "Uma fonte única de verdade — o banco — alimenta tanto o dashboard quanto a IA. Os dados entram via ETL e, a partir do banco, o fluxo se divide em duas camadas: visualização no Power BI e a camada de IA. Como os dois leem o mesmo banco, os números sempre batem."

---

## Slide — "A Inteligência Artificial que Transforma Decisões"
**Imagem:** `arquitetura_ia.png`.

**Tópicos (bullets):**
- **Persona "Ana":** analista de BI que responde com evidência — nunca de forma genérica.
- **Tool Calling:** o modelo (Gemini) gera uma consulta SQL, nós executamos no banco e ela responde com o **número real**. Como o dado vem de uma consulta, é impossível alucinar.
- **RAG:** camada extra sobre um documento de regras de negócio (definições, políticas, playbooks). A Ana **combina a regra com o dado**.
- **Grounding obrigatório:** nunca responde sem consultar o banco; sempre cita a fonte (a consulta executada).
- **Honestidade:** se o dado não existe, diz "não é possível concluir" em vez de inventar.

**Fala-chave:** "Duas técnicas de IA aplicada: tool calling para os dados estruturados e RAG para o conhecimento de negócio."

---

## Slide NOVO 1 — Deploy: a solução no ar
**Título:** Deploy — a solução publicada

**Tópicos:**
- App da Ana **publicado no Streamlit Community Cloud** — link público.
- **Acesso 24/7:** o avaliador conversa com a Ana a qualquer hora, sem instalar nada.
- Banco **versionado no repositório**; em produção o app apenas lê (somente leitura).
- **Chave da IA protegida** em "Secrets" — fora do código e do GitHub.
- **Resiliência:** retry automático + fallback de modelo se houver instabilidade.

**Fala:** "Deploy não era obrigatório, mas fiz para tornar a solução tangível: é só abrir o link e usar."

**Visual sugerido:** um print do app + a URL `https://projeto-desafio-capgemini.streamlit.app` em destaque.

---

## Slide NOVO 2 — A Ana onde o cliente está
**Título:** A Ana em qualquer canal (Telegram e além)

**Tópicos:**
- A **mesma Ana**, agora também num **bot de Telegram**.
- **Núcleo desacoplado do canal:** web e Telegram chamam a mesma função `perguntar()`.
- **Plugável em qualquer canal** — WhatsApp, Slack, Teams — **sem refazer a lógica de IA**.
- Visão de produto: "conecte seus dados, escolha o canal, a inteligência é a mesma".
    
**Fala:** "Como a camada de IA é desacoplada, levar a Ana para o WhatsApp ou Slack é só trocar a casca — o cérebro continua o mesmo."

**Visual sugerido:** o ícone do Telegram conectado ao "núcleo da Ana", com WhatsApp/Slack/Teams ao lado (mais apagados) apontando para o mesmo núcleo. Ideia de "hub central, vários canais".

---

## Onde encaixar os 2 slides novos no deck
Sugestão de ordem: ... → slide da IA (Ana) → **Deploy** → **A Ana em qualquer canal** → slide final (Decisões/Limitações). Assim os diferenciais aparecem logo depois da estrela (a IA) e antes do fechamento.
