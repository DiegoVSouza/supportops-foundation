# Continuidade do candidato financiado

## Estado

A fase 019 vincula novas tentativas exclusivamente ao candidato `free-dev-c2`, etapa `development`, com doze casos existentes e três tentativas independentes por caso. O teto primário é 136 chamadas, 278.528 tokens de entrada e 34.816 de saída. A confirmação permanece protegida em 60 chamadas, 122.880 tokens de entrada e 15.360 de saída. O saldo após as 16 chamadas históricas financia exatamente 36 tentativas C2 e 84 tentativas de holdout posteriores. As 24 tentativas não executadas de `free-dev-c1` continuam pertencendo ao candidato antigo e não podem ser retomadas ou transferidas.

Antes de preparar arquivos de campanha ou um cliente live, o P00 compara o hash canônico da política com o registry compartilhado, confere o UUID registrado com a identidade do ledger autoritativo e bloqueia enquanto existir o marker de migração pendente. O dispatch permanece bloqueado até a fase 005 do root reconciliar a migração autorizada. A interface privada usa o armazenamento protegido existente; esta fase não muda a UI nem chama o provider.

Gates offline da implementação: 34 testes focados e 142 testes no gate travado, além de lint, formato, compilação, contrato determinístico do dataset e configuração Compose. Os serviços locais opcionais permanecem INCOMPLETE. Nenhum desses resultados demonstra qualidade live. As revisões humana, independente, de dataset/rubric e promoção continuam PENDING.

## Pergunta de entrevista

**Português:** Como você impede que um candidato corrigido herde resultados antigos ou ultrapasse o orçamento?
O executor vincula o live a um único ID e etapa, rejeita o resume antigo por proveniência, conta todo o histórico uma vez no ledger cumulativo e separa o teto primário da confirmação. Antes do provider, também exige o hash de política aplicado e o UUID correto do ledger. Um marker durável bloqueia dispatch durante recuperação de migração.

**English:** How do you prevent a corrected candidate from inheriting old results or exceeding its budget?
The runner binds live execution to one campaign ID and stage, rejects the old resume on provenance, counts all history once in the cumulative ledger, and keeps the primary ceiling separate from confirmation. Before provider initialization it also requires the applied policy hash and matching ledger UUID. A durable marker blocks dispatch while a migration is being recovered.
