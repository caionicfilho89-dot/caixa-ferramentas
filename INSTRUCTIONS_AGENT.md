> 🧭 **Leia primeiro [AGENTS.md](AGENTS.md)** — arquivo mestre com objetivo, regras e estado atual. Em conflito, vale o AGENTS.md.

# Instruções para o Próximo Agente - Manutenção da Caixa de Ferramentas

Você assumiu o comando da "Fábrica da Caixa de Ferramentas". O objetivo é tornar esta a **maior caixa de ferramentas offline do mundo**. 

## Protocolo de Operação
- **Modo Capitão**: Você é o líder. Não peça permissão para implementar ideias de alta utilidade, siga o fluxo de *Brainstorming -> Seleção -> Execução -> Integração*.
- **Estrutura**: Siga rigorosamente o padrão existente:
  - Pasta da ferramenta: `caminho-da-ferramenta/`
  - Core: `xx_core.py` (lógica backend, salvar/carregar dados).
  - GUI: `xx_gui.pyw` (PyQt6, estilo QSS consistente com o resto da Caixa).
  - Prefixo: Use prefixos de 2-3 letras para evitar colisões (ex: `fa_`, `cg_`, `rc_`, `car_`, `hb_`, `sb_`, `dd_`, `gd_`, `as_`, `pm_`).
- **Registro**: Toda nova ferramenta **deve** ser adicionada em:
  1. `caixa-ferramentas/caixa.pyw` (na lista `BUILTIN`).
  2. `caixa-ferramentas/build_suite.py` (no dicionário `TOOLS`).

## Próxima Rodada: Rodada 14 — execução resiliente
As cinco ferramentas planejadas já estão registradas em `CLAUDE.md`; não gere outra lista de ideias nem faça uma varredura de todas as pastas para redescobrir o plano.

- Ordem planejada: scanner-documentos, gerador-graficos, compartilhar-rede, diario-criptografado, quadro-branco-colaborativo.
- Para Gemini CLI via Kilo Free: implemente **uma ferramenta por conversa**, sem subagentes ou execução paralela. Comece apenas pela primeira ferramenta ainda não concluída.
- Acesse somente a pasta da ferramenta atual e os arquivos de integração estritamente necessários. Liste cada pasta uma vez; reaproveite a listagem e não releia caminhos já vistos.
- Ao terminar uma ferramenta, rode os testes/validações aplicáveis, registre status, arquivos alterados, testes e próximo item em `BACKLOG.md`, e pare. Só inicie o próximo item depois de uma nova solicitação do usuário.
- Se atingir limite, repetir chamadas ou faltar contexto, pare sem reenviar o histórico. Salve um checkpoint curto em `BACKLOG.md` para retomar numa sessão limpa.

## Regras de Segurança e Qualidade
- **Ofuscamento/Segurança**: Mantenha os dados sensíveis (cofres, 2FA) criptografados.
- **Não Colisão**: Antes de criar algo, verifique em `caixa.pyw` se já não existe.
- **Validação**: Sempre execute `python build_suite.py --stage-only` após integrar uma nova ferramenta para garantir que a estrutura está correta e não há colisões.
- **Commit/Feedback**: Mantenha o usuário informado, mas seja proativo na implementação.

**Fábrica operando a todo vapor. Prossiga.**
