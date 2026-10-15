# P00 — SupportOps Foundation

## Contratos e arquitetura

O produto é uma biblioteca instalável com quatro partes: modelos de domínio, gerador determinístico, protocolo LLM e testkit. Consumidores usam artefatos versionados e registram commit de origem e SHA-256; import por caminho de repositório irmão cria acoplamento invisível e não é permitido.

Os modelos rejeitam campos extras e validam invariantes úteis a todos os consumidores. Mudanças incompatíveis passam por ADR, versão major e atualização explícita dos consumidores. O contrato inicial foi congelado em `1.0.0`; a versão atual `1.0.1` corrige a reconciliação de gasto live sem alterar assinaturas públicas.

## Fake, replay e live

- **Fake:** resposta roteirizada e determinística, útil para testar fluxo e decisões sem rede.
- **Replay:** reproduz chamadas gravadas em JSONL com correspondência exata e ordem; falha em miss/divergência. Cassettes podem conter prompts sensíveis e precisam de revisão/redação.
- **Live:** usa endpoint compatível explicitamente configurado, credencial, modelo, preço verificado e orçamento positivo. Reserva estimativa antes do transporte. Testes substituem o transporte e não usam provedor real.

Mesmo o modo live não mede qualidade automaticamente. Golden fixtures sintéticas validam comportamentos predefinidos; custo, latência e qualidade reais continuam `PENDING` sem uma execução real autorizada e rastreável.

## Determinismo e conjunto de teste

Uma seed gera os mesmos 40 clientes, 200 tickets, 30 artigos, 80 faturas e 60 casos dourados. JSON canônico e SHA-256 tornam alterações auditáveis. Casos de borda cobrem injeção de prompt, abuso/duplicidade de reembolso, takeover de conta, exposição de cartão, ameaça e indisponibilidade. Não se altera resultado esperado para mascarar regressão.

## Entrevista / Interview

**EN — Why use replay?** Replay provides repeatable regression checks for an exact request/response pair while isolating tests from provider availability and spend. It does not establish model quality.

**PT — Por que usar replay?** Replay fornece regressão reproduzível para pares exatos de requisição/resposta e isola os testes da disponibilidade e do custo do provedor. Ele não comprova qualidade do modelo.

**EN — How are public changes managed?** A breaking domain change needs an ADR, a major package version, artifact provenance, and explicit consumer updates.

**PT — Como mudanças públicas são gerenciadas?** Uma alteração incompatível exige ADR, versão major do pacote, proveniência do artefato e atualização explícita dos consumidores.
