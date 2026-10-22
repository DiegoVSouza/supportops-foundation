# SupportOps Foundation

SupportOps Foundation reúne o vocabulário que os projetos SupportOps precisam compartilhar: modelos de domínio, fixtures reproduzíveis, testkit e contratos de LLM independentes de provedor.

Versão atual do contrato: **1.0.1**. Consumidores devem registrar o commit de origem e o SHA-256 do wheel local instalado.

## Instalação e validação

Requisitos: Python 3.13 e uv 0.12.7.

```powershell
uv sync --locked
$env:LLM_MODE = "fake"
uv run --locked python scripts/check_full.py
uv run --locked python demo/foundation_demo.py
```

## Domínio e conjuntos de teste

`supportops_foundation.domain` exporta modelos Pydantic estritos para clientes, tickets, faturas, artigos, chamadas/resultados de ferramentas, execuções de agente e decisões de triagem. Campos desconhecidos são rejeitados. Datas de tickets precisam de fuso horário; valores de fatura devem ser positivos. Alterações públicas exigem ADR, atualização de versão e atualização explícita dos consumidores.

`generate_dataset(seed=42)` sempre produz os mesmos clientes, tickets, faturas, artigos e casos dourados. O JSON canônico e o SHA-256 deixam a mudança de fixture visível no diff. Esses casos testam contratos; não medem a qualidade de um modelo.

## Modos de LLM

- `fake` é determinístico e padrão em testes e CI.
- `replay` lê cassettes JSONL rastreáveis em ordem e falha com divergência ou esgotamento.
- `live` é opcional e requer `LLM_BASE_URL`, `LLM_API_KEY`, `LAB_MAX_USD` positivo, modelo explícito e preços por token verificados pelo chamador. O orçamento é reservado antes do transporte. Os testes injetam transporte e não acessam provedores.

Para adicionar um cassette, use uma linha JSON por chamada com `request` e `response` exatos, seguindo `tests/fixtures/replay/hello.jsonl`. Registre a origem e a revisão de redação de dados ao lado dos cassettes; prompts podem conter dados sensíveis. Chamadas live dependem de autorização explícita de orçamento.

## Serviços locais

`docker-compose.base.yml` define Postgres com pgvector, Redis e LocalStack para uso local. `scripts/doctor.py` informa o que realmente está disponível na máquina. A validação do Compose só verifica a configuração; não executa um teste E2E.

## Desenvolvimento

```powershell
uv run --locked python scripts/check_fast.py
uv run --locked python scripts/check_full.py
uv run --locked python scripts/doctor.py
```

Não altere expectativas do conjunto dourado para fazer testes passarem. Revise em conjunto seed, comportamento esperado e digest. Qualidade do modelo, custo de provedor e latência live ficam **PENDING** até execuções reais autorizadas.
