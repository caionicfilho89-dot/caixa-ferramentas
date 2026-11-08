> 🧭 **Leia primeiro [AGENTS.md](AGENTS.md)** — arquivo mestre com objetivo, regras e estado atual. Em conflito, vale o AGENTS.md.

# Gemini CLI — Caixa de Ferramentas

Fale em pt-BR informal e siga também `CLAUDE.md` e `INSTRUCTIONS_AGENT.md`, exceto onde o modo de baixo consumo abaixo os substitui para o Gemini CLI via Kilo Free.

## Gemini CLI via Kilo Free — modo de baixo consumo

- Faça somente o escopo explícito da solicitação atual, uma ferramenta por conversa. “Continue” não inicia outra rodada nem autoriza implementar cinco apps automaticamente.
- Não crie subagentes nem faça fan-out paralelo nesta rota gratuita. Pare ao concluir o item pedido e entregue um resumo curto.
- Para tarefas da Caixa, o workspace deve ser `C:\Users\caion\caixa-ferramentas`; nunca trate `~`/`C:\Users\caion` como raiz do projeto nem enumere a pasta pessoal inteira.
- Chame `ReadFolder` no máximo uma vez por caminho por tarefa. Uma listagem bem-sucedida é definitiva; reutilize o resultado e não volte a listar a mesma pasta.
- Leia só arquivos diretamente relevantes. Não varra pastas irmãs nem releia caminhos já vistos. Após cinco chamadas de leitura sem progresso, pare e explique o que falta.
- Antes de cada ferramenta, confira as três últimas chamadas; se caminho e operação já apareceram, não repita. Em caso de loop, interrompa e resuma imediatamente.
- Para tarefa nova ou histórico grande, use `/clear` e comece com um escopo pequeno. Não reenvie todo o histórico nem todos os arquivos do projeto.

## Mudanças seguras e enxutas

- Antes de editar, confira `git status --short` e leia apenas os arquivos/trechos relevantes. Preserve alterações existentes e não reescreva arquivos inteiros para uma correção localizada.
- Faça o menor patch que resolva o problema. Evite cadeias de scripts `replace`; inspecione o texto exato antes de substituí-lo.
- Em strings Unicode no Python, use UTF-8 literal ou um escape de ponto de código completo como `\U0001F4C8`. Não monte emojis com pares substitutos `\ud83d` + `\udc..`.

## Parada anti-loop

- Depois de editar, revise o diff e rode a validação mais estreita que serve para a mudança.
- Se falhar, leia o erro e o estado atual antes de tentar outra vez. Nunca repita a mesma chamada/escrita sem mudar a causa.
- Se a mesma correção falhar duas vezes, surgir aviso de loop ou as ferramentas começarem a repetir a mesma região/ação sem progresso, pare imediatamente. Informe o que mudou, o que foi validado e o próximo passo seguro; não continue tentando no escuro.
