# Ledger durÃ¡vel para campanhas locais

O runner P00 agora registra reservas e resultados em SQLite com journal WAL e `synchronous=FULL`. Cada trial tem eventos imutÃ¡veis `reserved` e `completed`; atualizaÃ§Ã£o e exclusÃ£o sÃ£o recusadas por triggers. A reserva Ã© gravada antes da futura chamada ao provedor. Se o processo cair depois da reserva, a tentativa fica incerta e o sistema nÃ£o a reexecuta automaticamente.

As contas cumulativas sÃ£o protegidas por `BEGIN IMMEDIATE`, que serializa leitura dos totais e nova reserva. Requests, tokens e custo estimado sÃ£o verificados antes da gravaÃ§Ã£o. Se o provedor nÃ£o informar uso, a reserva inteira continua contabilizada. O resumo JSONL exporta apenas IDs sintÃ©ticos, nÃºmeros, status e classes de erro; nÃ£o inclui prompt, resposta, headers ou raciocÃ­nio.

O lease usa lock do sistema operacional e arquivo com PID, host e ID de campanha, sem credenciais. Um segundo processo Ã© bloqueado enquanto o lease estÃ¡ ocupado; o sistema operacional o libera quando o processo dono termina. O helper ainda nÃ£o estÃ¡ ligado ao dispatch nem integrado a todos os seis launchers.

O dry-run roda em Python `-S` com biblioteca padrÃ£o. Ele continua mostrando os seis casos piloto e os limites `PENDING`; a execuÃ§Ã£o retorna INCOMPLETE antes de ler credenciais. O dispatcher Groq, o ledger/lease global entre projetos, revisÃ£o dos casos, quota grÃ¡tis, limites cumulativos, avaliaÃ§Ã£o e promoÃ§Ã£o continuam pendentes.

## Entrevista â€” portuguÃªs

**Como evitar que uma retomada cobre duas vezes uma chamada incerta?** Gravo a reserva antes do dispatch. Se o processo cair sem resultado confiÃ¡vel, mantenho a reserva como incerta e nÃ£o repito o trial automaticamente; uma reconciliaÃ§Ã£o explÃ­cita precisa resolver o estado.

## Interview â€” English

**How do you prevent resume from charging an uncertain call twice?** I persist the reservation before dispatch. If the process crashes without a reliable outcome, the reservation stays uncertain and the trial is not automatically repeated; explicit reconciliation must resolve it.
