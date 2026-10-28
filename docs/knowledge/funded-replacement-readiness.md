# Avaliação financiada e continuidade segura

A fase 028 concluiu 36 trials reais de desenvolvimento: 27 passaram no grader e nove falharam em três casos. O resultado é FAIL_PROVISIONAL. Os 148 testes offline aprovados verificam controles locais; não transformam esse resultado de qualidade em aprovação. O candidato avaliado, seu fingerprint, os recibos e as expectativas permanecem preservados.

A autorização de 13 chamadas adicionais foi aplicada por migração que mantém UUID, históricos e reserva desconhecida. Depois das 36 chamadas, restam somente 84 de holdout e 60 de confirmação. Não se pode usar essas reservas para repetir falhas ou avaliar uma correção. A decisão seguinte exige revisão real do conflito entre prompt e contrato e financiamento explícito de desenvolvimento novo.

O timeout do socket limita operações bloqueantes, mas não garante prazo total. O processo pai precisa limitar a espera e encerrar o transporte; se o envio puder ter ocorrido, a reserva continua conservadora. Retry de teste local, repetição de GET de metadados e replay de completion são operações diferentes. Os controles atuais não repetem completions incertas nem falhas semânticas.

A revisão privada permite navegar sem provider, escapa texto não confiável, mantém proveniência e registra correções append-only com autoria/data. As 65 respostas/registros foram navegadas tecnicamente, sem criar uma anotação. Isso não equivale a revisão humana ou independência autenticada.

## Entrevista / Interview

**PT — Como demonstrar que a avaliação terminou sem aprovar o produto?** Concilio cada trial com recibo e ledger, preservo o exit 1 e as nove falhas, relato o denominador 27/36 e o intervalo por caso único. Mantenho os gates de revisão e holdout pendentes e documento a reserva disponível.

**EN — How can an evaluation finish without approving the product?** Reconcile every trial with its receipt and ledger, retain exit 1 and all nine failures, report 27/36 with unique-case uncertainty, and keep human, holdout and promotion gates pending.

Evidência: ../../artifacts/evidence/funded-replacement-028/final-analysis.md e ../../.planning/phases/028-funded-replacement/VERIFY.md.
