# Continuidade do candidato financiado

## Estado

A fase 019 vincula novas tentativas exclusivamente ao candidato `free-dev-c2`, etapa `development`, com doze casos existentes e três tentativas independentes por caso. O teto primário é 136 chamadas, 278.528 tokens de entrada e 34.816 de saída. A confirmação permanece protegida em 60 chamadas, 122.880 tokens de entrada e 15.360 de saída. O saldo após as 16 chamadas históricas financia exatamente 36 tentativas C2 e 84 tentativas de holdout posteriores. As 24 tentativas não executadas de `free-dev-c1` continuam pertencendo ao candidato antigo e não podem ser retomadas ou transferidas.

Antes de preparar arquivos de campanha ou um cliente live, o P00 compara o hash canônico da política com o registry compartilhado, confere o UUID registrado com a identidade do ledger autoritativo e bloqueia enquanto existir o marker de migração pendente. A fase 005 do root foi aplicada sem alterar o UUID nem os históricos. O dry-run agora confere a política aplicada e ambos os ledgers em modo somente leitura, sob os locks compartilhados; nenhuma credencial ou rede é usada. A interface privada usa o armazenamento protegido existente; esta fase não muda a UI nem chama o provider.

Gates offline da implementação: 57 testes focados e 144 testes no gate travado, além de lint, formato, compilação, contrato determinístico do dataset e configuração Compose. Os serviços locais opcionais permanecem INCOMPLETE. Nenhum desses resultados demonstra qualidade live. As revisões humana, independente, de dataset/rubric e promoção continuam PENDING.

Após o commit do guard autenticado do root `8e03565`, o dry-run foi regenerado. A identidade congelada para a continuação é P00 source commit `dec99d750c9ff5482ee46c73aea3a26ba944eadf` + fingerprint completo `e53a13408600aa8d3faf8dfafa59192f5ede1f052866a81b22536e926e637488`; o fingerprint anterior `5d32a6c...` está arquivado como stale e não pode ser usado. O relatório atual mostra 36 chamadas C2, 84 de holdout futuro, 120 primárias P00, 60 confirmações protegidas, 16 usos históricos e as duas reservas desconhecidas sem somá-las. O preflight autenticado teve acesso ao modelo em quatro chaves, mas não recebeu cabeçalhos de limite e não informa billing tier ou saldo diário. Com autorização paga USD 0, a geração permanece BLOCKED até verificar Free tier; revisões dataset/rubric/humana/independente também seguem PENDING. Nenhum completion foi executado.

## Pergunta de entrevista

**Português:** Como você impede que um candidato corrigido herde resultados antigos ou ultrapasse o orçamento?
O executor vincula o live a um único ID e etapa, rejeita o resume antigo por proveniência, conta todo o histórico uma vez no ledger cumulativo e separa o teto primário da confirmação. Antes do provider, também exige o hash de política aplicado e o UUID correto do ledger. Um marker durável bloqueia dispatch durante recuperação de migração.

**English:** How do you prevent a corrected candidate from inheriting old results or exceeding its budget?
The runner binds live execution to one campaign ID and stage, rejects the old resume on provenance, counts all history once in the cumulative ledger, and keeps the primary ceiling separate from confirmation. Before provider initialization it also requires the applied policy hash and matching ledger UUID. A durable marker blocks dispatch while a migration is being recovered.
