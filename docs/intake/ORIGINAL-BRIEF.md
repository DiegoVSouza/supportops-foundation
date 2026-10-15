# P00 — Fundação compartilhada

## Objetivo
Criar a base que permite paralelismo seguro: workspace Python, contrato de domínio, cliente LLM com modos determinísticos, kit de testes e dataset sintético do **SupportOps Desk**.

## Entregáveis
- `pyproject.toml` raiz (uv workspace) + `Makefile` raiz (`doctor`, `lint`, `test`, `verify`).
- `shared/domain`: modelos Pydantic v2 `Customer`, `Ticket`, `TicketCategory`, `Priority`, `Invoice`, `KBArticle`, `ToolCall`, `ToolResult`, `AgentRun`, `TriageDecision`.
- `shared/llm`: `LLMClient` (Protocol) + `FakeLLM` (roteiro programável), `ReplayLLM` (cassettes JSONL), `LiveLLM` (provedor configurável por env, com limite `LAB_MAX_USD`). Contagem de tokens e custo estimado por chamada.
- `shared/testkit`: gerador sintético com seed (200 tickets, 30 artigos KB, 40 clientes, 80 faturas), **golden set** de 60 tickets com decisão esperada (categoria, prioridade, ação, escalonar sim/não), fixtures pytest.
- `docker-compose.base.yml`: Postgres+pgvector, Redis, LocalStack (SQS/SNS).
- `.github/workflows/ci.yml` básico (lint + `make verify`, `LLM_MODE=fake`).
- `.env.example`.
- `projects/pXX/Makefile` template com `verify`.

## Public API
```python
# shared.llm
class LLMClient(Protocol):
    def complete(self, messages: list[Message], *, schema: type[BaseModel] | None = None,
                 tools: list[ToolSpec] | None = None, model: str | None = None) -> LLMResponse: ...
# LLMResponse: text, parsed, tool_calls, usage(input_tokens, output_tokens), cost_usd, latency_ms, model
def get_llm(mode: Literal["fake","replay","live"] | None = None) -> LLMClient  # lê LLM_MODE
```
Congelado ao fim de P00 (semver `1.0.0`). Mudança = ADR.

## Fases
- **001 domain+testkit** — Wave 1: domain ∥ gerador de dados; Wave 2: golden set + fixtures.
- **002 llm** — Wave 1: Fake+Replay; Wave 2: Live com orçamento e cassette recorder.
- **003 infra** — Wave 1: compose base ∥ CI; Wave 2: `make doctor` (checa Docker, portas, versões).

## Verificação
- `make verify` verde em máquina limpa em `LLM_MODE=fake`.
- Gerador é determinístico: mesmo seed → mesmo hash do dataset (teste).
- `LiveLLM` sem chave **falha explicitamente**, não cai em fake silenciosamente (teste negativo).
- `ReplayLLM` falha se a cassette não tem a chamada (teste negativo).
- Golden set tem ≥10 casos de fronteira (ex.: prompt injection embutido no ticket, cliente inadimplente, pedido de reembolso acima do limite).

## README exigido
`README.md` do monorepo atualizado + `shared/README.md`: como usar os 3 modos, como regravar cassettes, esquema do dataset, como adicionar um caso ao golden set.

## Documentação de conhecimento
`docs/knowledge/P00-foundation.md`: por que fake/replay/live; determinismo em testes de LLM; contratos congelados; modelagem do domínio.

## Fora de escopo
Qualquer lógica de agente, API HTTP, observabilidade, deploy.
