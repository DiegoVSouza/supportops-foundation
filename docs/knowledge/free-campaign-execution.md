# Campanha local restrita ao plano gratuito

A autorização de 2026-10-26 permite a avaliação sintética no plano gratuito e adia a revisão humana para depois da preparação técnica. O gasto pago continua zero. Tetos econômicos calculados pelos preços de referência não são uma fatura ou autorização de cobrança. O helper compartilhado usa apenas as chaves numeradas do `.env` da raiz, confirma o catálogo e contabiliza cada tentativa nos logs de uso do projeto, consultando os seis logs antes de liberar outra chamada.

O CLI exige `LLM_MODE=live` e `--execute-free`. Sem ambos, não inicia o provedor. O dry-run permanece sem credenciais e funciona com Python `-S`. Cada lote executa até dez novas tentativas, usa o lock comum do lab e para em limite, quota ou falha operacional. Retomar não repete falhas semânticas ou tentativas incertas.

O manifesto fixa hashes de fontes públicas, dataset, prompt, configuração e política compartilhada. Nenhuma chave é hasheada. Uma mudança de prompt ou runtime exige outro candidato; commits apenas de artifacts/docs podem ser registrados sem fingir que o código mudou. O relatório usa intervalos de Wilson por caso com os três resultados, e mostra separadamente trials, casos incompletos, falhas operacionais e fatias por domínio, família e idioma.

As respostas sintéticas originais ficam somente no banco privado `.runtime/llm-review/answers.sqlite`, fora do Git e dos artifacts, para a aplicação de revisão humana. O diretório recebe ACL apenas do usuário atual no Windows e permissões de proprietário nos demais sistemas. Os artifacts contêm decisões discretas, presença de justificativa, resultados sanitizados, referências e consumo; não contêm justificativas livres ou raciocínio interno. A interface de revisão será ligada a esse banco em uma fase posterior.

Na preparação offline, 111 testes do gate completo passaram, incluindo a prova de que o subprocesso usa UTF-8 e não herda chaves do ambiente. A maior reserva conservadora renderizada nos 40 casos foi 1.555 tokens de entrada, abaixo do teto mantido de 2.048. Isso é evidência de controle e planejamento, não qualidade do modelo real. Revisão humana, campanha completa, verificação independente e promoção permanecem INCOMPLETE até seus próprios resultados.

## Entrevista — PT-BR

O primeiro piloto real (`free-pilot-v1`) parou após quatro requisições: três respostas falharam no roteamento esperado e uma falha operacional interrompeu o lote. O baseline foi preservado; o holdout não foi usado. O consumo conhecido é 844 / 248 tokens; a reserva conservadora da tentativa com uso desconhecido mantém o total contabilizado em 2.319 / 504. Esse resultado é INCOMPLETE, não aprovação. O próximo trabalho deve corrigir a observabilidade do erro e esclarecer a política geral do prompt em uma rodada de desenvolvimento declarada.

**Como preparar uma revisão posterior sem salvar conteúdo bruto nos artifacts?** Guardo somente respostas sintéticas autorizadas em estado privado da aplicação de revisão, com controle de acesso, e publico apenas resultados sanitizados e referências. Não crio cassettes live nem repito chamadas para obter uma amostra melhor.

## Interview — English

**How do you support deferred review without raw content in artifacts?** I keep only authorized synthetic answers in private review-application state with access controls, and publish sanitized results and references. I do not create live replay cassettes or resample failures for a better answer.
