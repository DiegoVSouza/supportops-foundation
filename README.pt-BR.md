# SupportOps Foundation

<!-- case:start -->
## O case

- **Problema.** Serviços independentes precisam do mesmo vocabulário de ticket, fatura e ferramenta, e de um jeito honesto de testar um modelo contra ele.
- **Decisão.** Contratos Pydantic estritos, dataset com semente e digest, e um só ledger de orçamento entre `fake`, `replay` e `live`. O orçamento é reservado antes de qualquer chamada ao provedor.
- **Medido.** Uma campanha de desenvolvimento com modelo real: 27 de 36 trials passaram, 9 de 12 casos únicos passaram nos três trials (intervalo de Wilson 95% de 0,47 a 0,91). Veredito `FAIL_PROVISIONAL`. Fonte: `artifacts/evals/live/free-dev-c2r1/report.json`. O orçamento de holdout (84 chamadas) e o de confirmação (60) não foram tocados.
- **Como rodar.** `uv sync --locked && uv run --locked python scripts/check_fast.py`
- **Limites.** A biblioteca entrega contratos e fixtures. Fixture não é qualidade de modelo, e revisão humana e promoção seguem pendentes.
- **Docs.** [Arquitetura](docs/architecture.md), [decisões](docs/decisions).
<!-- case:end -->

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

## Campanha gratuita local

O dry-run não acessa credenciais: `python -S scripts/run_live_campaign.py --stage pilot --dry-run`. A avaliação autorizada exige `LLM_MODE=live` e `--execute-free`, usa os tetos compartilhados gratuitos da conta e mantém gasto pago zero.

```powershell
$env:LLM_MODE="live"
uv run --locked python scripts/run_live_campaign.py --stage pilot --campaign-id free-pilot-v1 --execute-free --max-trials 6
uv run --locked python scripts/run_live_campaign.py --resume free-pilot-v1 --execute-free
```

Cada lote tem até dez novas tentativas. Falhas concluídas não são repetidas; tentativas incertas exigem reconciliação. Resultados sanitizados e comandos de retomada ficam em `artifacts/evals/live/<campaign-id>/`. Respostas sintéticas para revisão posterior ficam somente no banco privado da aplicação, fora do Git/artifacts. Exit 0/1 indica aprovação/falha provisória de engenharia; exit 2 indica bloqueio, interrupção ou checkpoint de consumo. Revisão humana e promoção continuam pendentes.
