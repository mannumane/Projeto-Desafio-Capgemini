# Manual de Regras de Negócio — Varejo

Documento de referência usado pela camada de RAG. A persona "Ana" consulta
este material para complementar a análise dos dados com contexto, definições e
políticas da empresa. As regras aqui descritas são premissas de negócio
(não vêm do banco de dados).

## Glossário de métricas

- **Receita**: soma do valor de vendas (campo `sales`). Não desconta custos.
- **Lucro**: resultado após custos e descontos (campo `profit`).
- **Margem**: lucro dividido pela receita, em percentual. Margem saudável de referência para o varejo é acima de 10%.
- **Ticket médio**: receita dividida pelo número de pedidos. Mede o valor médio por compra.
- **Pedido**: identificado por `order_id`; pode conter vários itens.

## Definição dos segmentos RFM

A segmentação RFM classifica clientes por Recência (quão recente foi a última compra), Frequência (quantas compras) e Valor monetário (quanto gastou).

- **Campeões**: melhores clientes (alta recência, frequência e valor). São prioridade de retenção e candidatos a programas de fidelidade e benefícios exclusivos.
- **Leais**: compram com regularidade e bom valor. Estratégia: aumentar ticket via cross-sell e up-sell.
- **Promissores**: clientes recentes com potencial. Estratégia: nutrir com ofertas de entrada e onboarding.
- **Em risco (alto valor)**: já foram valiosos, mas estão sumindo. Estratégia: campanhas de reativação prioritárias, pois o valor em jogo é alto.
- **Perdidos**: baixa recência e baixo valor. Estratégia: campanhas de baixo custo; não priorizar investimento alto.
- **Atenção**: comportamento intermediário; monitorar.

## Política de descontos

- Descontos de até 20% são considerados saudáveis e dispensam aprovação.
- **Descontos acima de 20% exigem aprovação gerencial**, pois historicamente corroem a margem e podem gerar prejuízo.
- Descontos só devem ultrapassar 20% com justificativa estratégica clara (girar estoque parado, conquistar cliente de alto potencial, ação sazonal planejada).
- Meta: manter o desconto médio da operação abaixo de 10%.

## Playbook de retenção

- Concentrar esforço de retenção nos segmentos **Campeões** e **Em risco (alto valor)**, pois representam a maior parte da receita.
- Regra prática (princípio de Pareto): uma fração pequena de clientes costuma concentrar a maior parte da receita; ações focadas nesse grupo tendem ao maior retorno.
- Reativação de "Em risco" deve acontecer em até 90 dias da queda de atividade.

## Estratégia regional

- Regiões com maior receita merecem manutenção de nível de serviço; regiões de menor receita são oportunidades de expansão.
- Avaliar custo de frete por região: frete alto pode reduzir a margem e piorar a experiência.

## Boas práticas de leitura de dados

- Sempre comparar um número com uma referência (meta, média, período anterior) antes de concluir.
- Receita alta com margem baixa pode indicar excesso de desconto ou mix de produtos pouco lucrativos.
- Não confundir volume (quantidade vendida) com rentabilidade (lucro).
