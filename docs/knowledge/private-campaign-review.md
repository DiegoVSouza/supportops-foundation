# Revisão privada de campanhas

A interface local lê respostas sintéticas do SQLite protegido em modo somente leitura. Cada item mantém o vínculo com campanha, candidato, caso, trial e versões de prompt, schema, dataset e rubric. O piloto histórico antecede o schema separado; registrar essa ausência é mais correto do que inventar um hash retrospectivo.

O conteúdo da resposta é texto não confiável: escaping e CSP impedem HTML ativo, scripts e recursos externos. O servidor aceita apenas loopback, exige um segredo por sessão e não carrega o `.env` nem inicializa provider. A autenticação local não transforma uma anotação em aprovação de promoção.

As anotações são privadas e append-only. Elas preservam usuário do sistema, identidade/posição declarada pelo revisor, data, versões e referência à anotação corrigida. Discordâncias permanecem visíveis. A amostragem usa casos únicos, estratos de família/idioma e candidatos separados; trials de um candidato não financiam nem comprovam a qualidade de outro.

A reconciliação confirmou 16 chamadas, com uso conhecido de 5.236 tokens de entrada e 1.650 de saída. A tentativa desconhecida continua reservada: 2.048/256 no ledger lógico e 1.475/256 no transporte. Esses ledgers descrevem as mesmas chamadas e não devem ser somados. O novo candidato precisa de 120 chamadas primárias; restam 110. Também faltam 370 tokens de saída para sua reserva máxima, mantendo a confirmação protegida. Não houve geração adicional.

## Entrevista — português

**Como você preserva a rastreabilidade da revisão humana?** Cada anotação vincula caso, tentativa, candidato e versões congeladas, registra autoria e data e não pode substituir uma anotação anterior. Correções são novos registros, e divergências continuam auditáveis. Os gates humanos permanecem pendentes até uma revisão real.

## Interview — English

**How do you preserve human-review provenance?** Each append-only annotation binds the case, trial, candidate and frozen revisions and records its author and timestamp. Corrections reference earlier notes instead of replacing them, preserving disagreement. Human approval remains pending until an actual reviewer completes the required coverage.
