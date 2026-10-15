# Interview preparation: SupportOps Foundation

## English

### Why separate a domain package from the applications?

Independent repositories can install a versioned wheel and test against the same explicit vocabulary. This avoids sibling path imports and makes contract changes visible through semantic versions, ADRs, provenance, and consumer upgrades.

### How do you test an LLM workflow without making paid calls?

The client protocol has deterministic fake and cassette replay implementations. The live adapter receives an injectable transport and checks a spend cap before transport. CI uses fake mode; live quality and cost stay pending until an authorized, traceable run exists.

### What does the golden set prove?

It proves deterministic fixture generation and regression behavior for known cases. It does not prove model quality. Quality claims require real runs, documented criteria, and reproducible traces.

## Português

### Por que separar o pacote de domínio das aplicações?

Repositórios independentes podem instalar um wheel versionado e testar o mesmo vocabulário explícito. Isso evita imports de diretórios irmãos e torna mudanças visíveis por versões semânticas, ADRs, proveniência e atualização dos consumidores.

### Como testar um fluxo com LLM sem chamadas pagas?

O protocolo do cliente oferece fake determinístico e replay de cassettes. O adaptador live recebe transporte injetável e verifica o limite de gasto antes do transporte. CI usa fake; qualidade e custo live ficam pendentes até uma execução autorizada e rastreável.

### O que o conjunto dourado comprova?

Comprova geração determinística de fixtures e regressão para casos conhecidos. Não comprova qualidade de modelo. Afirmações de qualidade exigem execuções reais, critérios documentados e traces reproduzíveis.
