# Lotes limitados e retomada conservadora

O controlador `scripts/campaign_batch.py` executa até dez novas tentativas por lote usando o ledger e o lock de processo existentes. Ele valida os tetos cumulativos e por tentativa, exige aprovação explícita de um guard de conta antes de reservar e salva o checkpoint antes de executar o callback. O callback deve fazer uma única tentativa e devolver somente resultado, classificação de erro e consumo sanitizados.

Falhas semânticas são resultados concluídos: ficam preservadas e não são repetidas na retomada. Uma queda antes de salvar o resultado deixa a reserva incerta e impede novo despacho até reconciliação. Os testes encerram um processo abruptamente durante a execução e antes da persistência do resultado; o sistema libera o lock, mas o ledger continua cobrando a reserva. Se apenas a exportação falhar depois do resultado persistido, a retomada consulta o SQLite e não repete a tentativa.

Uso observado acima da reserva permanece registrado e interrompe o lote. Dados inválidos, guard indisponível, quota, limite cumulativo e prazo impedem novas tentativas. O prazo do controlador impede iniciar outra chamada; o timeout da chamada em andamento é responsabilidade do futuro adaptador. O launcher também precisa validar o manifesto e a revisão candidata congelados antes de retomar.

Foram executados 30 testes focados e 99 testes no gate completo offline, com exit 0. Isso comprova a lógica usando callbacks sintéticos. O CLI público continua bloqueado: a integração real com Groq, guard compartilhado entre os seis projetos, limites/aprovações e avaliação humana permanecem incompletos. Evidência: `artifacts/evidence/live-campaign-batches/`.

## Entrevista — PT-BR

**Como evitar consumo duplicado depois de uma queda?** Persista a reserva antes da chamada e o resultado antes de declarar conclusão. Na retomada, pule todos os resultados concluídos, incluindo falhas; bloqueie tentativas incertas até reconciliar. Uma fronteira de lote não zera o consumo cumulativo.

## Interview — English

**How do you avoid duplicate consumption after a crash?** Persist the reservation before the call and the result before claiming completion. On resume, skip every completed outcome, including failures, and block uncertain attempts until reconciliation. Chunk boundaries never reset cumulative consumption.
