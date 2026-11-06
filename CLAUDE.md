# 🧰 Caixa de Ferramentas — protocolo da "fábrica"

Meta do Caio: **a maior caixa de ferramentas offline do mundo**. Ele não pede ferramenta por
ferramenta — a fábrica roda sozinha seguindo `BACKLOG.md`. Fale com ele em pt-BR, informal.

## Papéis e economia de tokens
- **Capitão (sessão principal, modelo mais inteligente):** escolhe a rodada, escreve os briefings,
  REVISA cada app (roda testes, abre offscreen, lê o código crítico), corrige, integra, builda,
  commita/pusha, atualiza BACKLOG/CLAUDE.md/memória. Não escreve app inteiro sozinho.
- **Operários (subagentes):** constroem 1 app cada, em paralelo. Sempre `model: "sonnet"`
  (mais econômico). Rodadas de **5 apps**. Trabalhar dentro da disponibilidade de tokens:
  se o uso estiver apertado, rodadas menores (2–3) ou pausar e avisar o Caio.

## Estado atual (ATUALIZE ao fim de cada rodada)
- Caixa v1.4.0 = 23 ferramentas (selftest OK: 23), instalador `instalador\CaixaDeFerramentas-Setup-1.4.0.exe`.
  (v1.3.0 nunca virou instalador — pulou direto pra 1.4.0.) Release v1.4.0 PUBLICADA e os 6 repos
  (ferramentas-br, kit-hacker, ferramentas-dev, calculadora-clt, conversor-unidades, pix-boleto) criados.
- Limite de 5h de uso: se agentes caírem com 429, retomar cada um via SendMessage após o reset.
- Rodada 1 ✅ integrada: kit-hacker (20) · ferramentas-dev (16) · calculadora-clt (7) ·
  conversor-unidades (15 categorias) · pix-boleto (3 abas).
- Rodada 2 ✅ integrada no código (SEM build, 28 ferramentas no caixa.pyw): financas (fin_), tempo (tm_),
  notas-md (nm_), tarefas (tf_), calendario-br (cal_). Repos dessas 5 ainda não criados.
- Rodada 3 ✅ integrada (33 ferramentas): monitor-sistema (ms_), info-pc (ip_), inicializacao (ini_),
  compactador (cz_), cripto-arquivos (ca_). Repos das rodadas 2 e 3 a criar.
- Rodada 4 ✅ integrada (38 ferramentas): editor-imagem (ei_), gravador-voz (gv_), paletas (pl_), webcam (wc_),
  fontes (fn_). Repos da rodada 4 a criar.
- Rodada 5 ⏳ lançada: rede (rd_), sorteios (st_), saude (sd_), calculadora-cientifica (cc_), flashcards (fc_). (Expansor de texto saiu da rodada: exigiria hook global de teclado.)
  Depois dela o BACKLOG acaba → capitão escreve as rodadas 6+ no BACKLOG antes de seguir.

## Estrutura
- Cada ferramenta = pasta irmã em `C:\Users\caion\<pasta>` (BASE = pai desta pasta).
- GUI: `<nome>.pyw`; lógica em módulos com **PREFIXO ÚNICO** (kh_, fd_, clt_, cu_, pb_ …) — o
  `build_suite.py` achata tudo numa pasta só; nome repetido = COLISÃO e o build aborta.
- Registro na Caixa: tupla em `BUILTIN` (caixa.pyw) `(emoji, nome, descrição, pasta, script)` +
  entrada em `TOOLS` (build_suite.py). Pacote com dados/submódulos → `COLLECT_ALL`.
- Python: `C:/Python313/python.exe`. Build: `python build_suite.py` → `ISCC.exe instalador.iss`
  (Inno Setup em `%LOCALAPPDATA%\Programs`). Selftest: `dist\Caixa\Caixa.exe --selftest` = "OK: N".
- Versão: `APP_VERSION` em caixa.pyw + `MyAppVersion` em instalador.iss (sempre juntos).

## Briefing padrão do operário (colar no prompt de cada agente)
1. Pasta `C:\Users\caion\<pasta>\`, GUI `<nome>.pyw`, módulos com prefixo `<px>_`.
2. Cabeçalho `HERE=...; sys.path.insert(0, HERE)`; rodapé `def main()` + `if __name__ == "__main__"`.
3. Tema: copiar QSS de `C:\Users\caion\gps-falso\gps_falso.pyw` (accent #7c5cff, bg #11131a, `#go`).
4. UI pt-BR com acentos; identificadores ASCII; offline sempre que possível; stdlib preferida.
5. NÃO tocar em outras pastas (principalmente `caixa-ferramentas`).
6. GOTCHA: a tool Write injeta às vezes letras de outro alfabeto → py_compile + varrer
   `0x0300<=ord(c)<=0x1CFF` em todos os arquivos.
7. Testes: py_compile, teste de lógica com valores conhecidos, smoke test GUI
   (`QT_QPA_PLATFORM=offscreen`, `PYTHONIOENCODING=utf-8`). Manter `test_<px>.py`.
8. README.md pt-BR, requirements.txt, .gitignore, LICENSE MIT (Caio, 2026), `git init` + commit
   terminando com a linha Co-Authored-By do SEU lembrete de atribuição (o modelo que você é). Sem push.
9. Relatório final: pasta, script, funções + contagem, testes, deps pip.

## Checklist do capitão ao fim da rodada
1. Pra cada app: rodar `test_<px>.py`, py_compile, conferir `git status` limpo.
2. Checar colisão de nomes entre módulos de todas as pastas do TOOLS.
3. Integrar (BUILTIN + TOOLS + COLLECT_ALL). **NÃO buildar o exe a cada rodada** (pedido do Caio):
   a Caixa via `caixa.pyw` já mostra as novas na hora. Build + instalador + release só quando o
   Caio pedir ("fecha uma versão") ou em marco grande. Aí: subir versão, `build_suite.py`, selftest, ISCC.
4. Commit + push da caixa-ferramentas. Repos novos: o Caio roda `gh repo create` via `!`
   (bloqueado pro Claude) — mandar UM comando com todos da rodada; depois `git push`.
5. (Só quando houver build) `gh release create vX.Y.Z` com o instalador — comando pro Caio colar.
6. Atualizar "Estado atual" aqui, BACKLOG.md e a memória `project_fabrica_caixa`.
7. Disparar a próxima rodada (sem perguntar), se houver tokens.

## Limites
- Nada que sirva pra golpe ou ataque a terceiros (ex.: boleto só CONFERIR, nunca gerar;
  Kit do Hacker só codificar/inspecionar, sem cracking/força bruta).
- Nunca apagar coisa do Caio com checagem "mais ou menos" — só verificação exata.
- Build falhando com "arquivo em uso" / Caixa.exe sumindo do dist: é uma Caixa ABERTA rodando de
  `dist\Caixa` (não o Defender). `Get-Process | ? Path -like '*caixa-ferramentas*'` e fechar antes.
  Nunca abrir a Caixa pra teste direto do dist — abrir pelo .pyw.
- Cuidado com sessões paralelas: antes de editar caixa.pyw/build_suite.py, `git status`/mtime
  pra ver se outra sessão está mexendo (já aconteceu em 2026-11-05).
