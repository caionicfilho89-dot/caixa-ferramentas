# 🧭 RUMO.md — o rumo novo da Caixa de Ferramentas (decisão do Caio, 2026-11-09)

> **Este arquivo manda mais que todos os outros** (`AGENTS.md`, `QUADRO.md`, `ESTACOES.md`,
> `AGENTS_PROTOCOL.md`, `BACKLOG.md`, `CLAUDE.md`, `GEMINI.md`, `INSTRUCTIONS_AGENT.md`).
> Onde eles falarem em "rodada de 6 ferramentas", "lane" ou "um milhão de funções", **vale o que está aqui.**

## ⛔ Calculadora nova: PAUSADA. Trabalho: NÃO para.

- **Ninguém cria ferramenta/pasta nova de calculadora.** As 750 que existem **ficam como estão**.
- **Mas ninguém fica parado.** Cada agente tem uma **FILA** própria (abaixo). Terminou uma tarefa? Pega
  a próxima da sua fila **na hora**, sem perguntar a ninguém e sem esperar ninguém.

## Por quê

O Caio abriu a Caixa e achou **genérica e irreal**: "tudo parece igual, calculadora de sei lá o quê,
não vejo utilidade". O motivo é a meta antiga (quantidade). Saíram 750 apps com a mesma fórmula:
formulário → número. Nenhum mexe nas coisas dele.
**Meta nova: a Caixa tem que ser útil pro Caio de verdade e ter cara própria.**

## O que vamos construir (as duas coisas juntas)

### 1. 🔎 Barra que responde tudo
- Uma barra no topo da Caixa (e atalho global **Ctrl+Espaço**, com a Caixa na bandeja).
- O Caio escreve do jeito dele: `ipva de um carro de 60 mil em SP`, `quanto rende 18 litros de tinta`,
  `20% de 350`, `troco de 100 pra 73,50`, `90 dias úteis a partir de hoje`.
- A **resposta aparece ali mesmo**, em uma linha, com "abrir a ferramenta completa" do lado.
- Por trás, ela chama a lógica que já existe nos `<px>_core.py`. **Reaproveita, não reescreve.**
- Se não entender, mostra as 5 ferramentas mais parecidas (nome/descrição/ajuda).

### 2. 🏠 Tela "Hoje" (o que importa no PC do Caio agora)
Primeira coisa que aparece ao abrir. A grade das 750 continua, a um clique ("Todas as ferramentas").
Cartões **vivos, com dados reais**, e cada um tem um botão que resolve:
- 💾 Disco: quanto falta no C:, o que mais cresceu → "liberar espaço".
- 📥 Downloads: arquivos soltos, instaladores velhos, duplicados → "arrumar".
- 🖼️ Prints recentes → copiar, anotar, extrair texto (OCR).
- 📋 Área de transferência: o que ele copiou por último.
- ⏰ Vencendo: garantias, validade de remédio/cosmético, contas fixas, assinaturas (dados que as
  ferramentas já salvam).
- 🍮 Pudim: "continuar assistindo" (config do PudimFlix) + abrir. 📺 TV / TeraBox: atalhos que funcionam.

Cartão sem dado real **não aparece**.

## 📋 Quadro de tarefas (ninguém parado) — 2026-11-10
Fila acabou ou nada pra fazer? `python painel.py <você> --pegar` dá a próxima tarefa livre do `tarefas.json` que combina
com você (fica marcada como sua). Terminou: `python painel.py <você> --concluir T07 "o que ficou pronto"` e `--pegar` de novo.
O carteiro manda esse aviso pra quem está parado há 10+ min; quando sobram < 5 livres, pede propostas ao Antigravity
(`python tarefas.py --nova "titulo" "detalhe" agente1,agente2`). Ver o quadro: `python tarefas.py`.

## 🎯 Tarefa tem que ser ÚTIL (Caio, 10/11 — o Antigravity fez 39 tarefas de nicho numa noite)
Antes de criar ou pegar tarefa: "o Caio usaria isso essa semana?". Se não, NÃO faça.
- Vale: problema real do CRITICA.md, ferramenta que ele usa (config `uses`), barra pras perguntas dele, Tendência do dia,
  esconder/juntar inútil (T23/T24), bug, velocidade, visual.
- NÃO vale: ligar adaptador de calculadora de nicho (vinho, bolo, laps, crochê…), ferramenta nova de calculadora,
  "mais cobertura" só pra subir número. Ficar parado é MELHOR que gastar cota com isso.

## 💸 Modo economia (decisão do Caio, 2026-11-10)

O `python painel.py` mostra no topo o modo de cada conta (medido a cada 3 min pelo carteiro via `economia.py`,
com **previsão**: se no ritmo atual a cota estoura antes de renovar, já entra em econômico).
Conta **Claude** = Claude. Conta **SuperGrok** (limite xAI unificado) = Cocaino + Grok CLI + Cursor. Antigravity: sem medidor (normal).
- 🟢 **normal**: siga a fila.
- 🟡 **econômico**: só tarefas pequenas e certeiras; nada de varrer pasta inteira, `grep` em tudo ou ler arquivo
  inteiro; `/new` entre tarefas; nada de build/teste pesado à toa; respostas curtas. O carteiro entrega no máx.
  1 vez a cada 10 min.
- 🔴 **crítico**: termine o passo atual, anuncie `--feito` com onde parou e **PARE** até a cota renovar
  (o painel mostra a hora). O carteiro não entrega pedido pra quem está em crítico.
**Orçamento do dia** (cotas semanais): o que sobrava à meia-noite ÷ dias até renovar. Chegou no orçamento do dia
→ 🟡; passou 25% dele → 🔴 até amanhã. Sobra de um dia vai pros próximos.
O Caio pode travar na mão: `python economia.py --forcar economico|critico|normal|auto`.
**Distribuição por folga** (Caio: "os com menos tokens fazem menos"): tarefa que dois podem fazer fica com quem tem mais
cota sobrando (`economia.folga_do_agente`); em 🟡 o carteiro empurra só a cada 30 min; em 🔴 ou RESERVA o `--pegar` não dá tarefa.

## 🔥 Tendência do dia (decisão do Caio, 2026-11-10)

A Caixa acompanha o que a comunidade dev está curtindo. Todo dia às 08:00 o `tendencias.py` lê GitHub Trending,
repositórios novos com mais estrelas, Show HN e Reddit, filtra só **ferramenta de PC** (sem isca de pirataria,
sem golpe/ataque, sem furar DRM, sem stalker) e escreve:
- `TENDENCIAS.md` — ranking do dia com "parecida na Caixa";
- `TENDENCIA_DO_DIA.md` — **a tarefa**: fazer a versão nossa, igual ou melhor.

**Quem faz:** o **Grok Build** é o dono da Tendência do dia. Cursor e Antigravity pegam se a fila deles acabar e o
Grok Build não tiver anunciado `--fazendo "Tendência: ..."` no painel. Isto **não** é calculadora: é a exceção
liberada à pausa. Regras: código escrito do zero (inspiração na ideia, nunca copiar código, por causa da licença),
offline, PyQt6, pt-BR, padrão de pasta/prefixo do `AGENTS_PROTOCOL.md`. Se já existe parecida
(`catalogo.py --check`), **melhore a nossa**. Terminou: `python tendencias.py --feita <url>` + `--feito` no painel;
o Claude integra.

**TODO DIA, SEM FALTA (Caio, 2026-11-11):** se às 08:00 não rodou, o carteiro roda o radar sozinho (checa a cada 10 min)
e cria a tarefa `🔥 Tendência do dia DD/MM` no quadro (grokbuild, antigravity). **Categoria 🔥 Tendências:** toda
ferramenta NOVA que nasce de tendência entra em `tendencias_caixa.json` (campo `pastas`) e aparece em 🔥 Tendências,
a 1ª categoria da Caixa. Melhorou uma que já existia? Não entra (continua na categoria dela).

---

## ⛔ PORTÃO DE QUALIDADE + QUADRO SEMPRE CHEIO (Caio, 2026-11-11)

**`--concluir` agora passa por `portao.py`.** A tarefa só vira "feito" se: (1) nada foi feito em `staged/` ou `dist/`
(cópia de build — o próximo build APAGA; foi o que perdeu o feriado de 20/11 da T66); (2) os testes das pastas de
ferramenta CITADAS no resultado passam; (3) ferramenta nova (com ENTREGA.json) está registrada em BUILTIN/TOOLS (a T68
ficou pronta mas invisível); (4) caixa.pyw e build_suite.py compilam. Recusou? A tarefa continua sua: conserte e
conclua de novo. **Cite sempre a pasta** (`C:/Users/caion/<pasta>`) no resultado.

**O quadro não esvazia mais:** `quadro_cheio.py` (carteiro, a cada 10 min) mantém ≥ 3 tarefas livres por agente
ativo com 🔥 Tendência extra (máx. 2/dia, do TENDENCIAS.md) e 🧪 lotes de QA (5 ferramentas do catálogo pra testar de
verdade e consertar). Parado com tarefa livre = falha sua.

---

## 📡 PAINEL — como um sabe o que o outro está fazendo

Cada agente tem **um arquivo só dele** em `painel/<agente>.json` e mexe nele **só pelo script**:

```
python painel.py                         # VER todo mundo: o que cada um faz, arquivos ocupados, pedidos pra você
python painel.py cursor --fazendo "F2: barra de busca" --arquivos caixa_busca_ui.py --proximo "F3"
python painel.py cursor --feito "F2: barra pronta, 9 testes OK"
python painel.py antigravity --pedir cursor "a UI precisa mostrar o campo detalhe"
python painel.py cursor --resolvido antigravity
python painel.py grok --bloqueado "não acho o exe novo"
```

**O ciclo de todo agente (sempre igual):**
1. `python painel.py <você>` → lê o que os outros estão fazendo e se tem 📨 pedido pra você.
2. Pedido pra você? Resolve primeiro (é rápido, e destrava o outro). Depois `--resolvido <quem pediu>`.
3. Pega a próxima tarefa da **sua FILA** e anuncia: `--fazendo "Fx: ..." --arquivos ... --proximo "Fy"`.
4. Faz, testa de verdade.
5. Anuncia: `--feito "Fx: o que ficou pronto + resultado dos testes"`. **Volta pro passo 1, sem parar.**

**Nunca esperar ninguém:**
- Depende de algo de outro agente que ainda não existe? **Use o contrato abaixo com um stub nos seus
  testes**, mande um `--pedir` e **siga**. Não fique parado esperando resposta.
- Travou de verdade? `--bloqueado "o motivo"` e **pule para a próxima tarefa da fila**. Volte nela depois.
- Fila acabou? Leia o `CRITICA.md` do Grok e conserte o que ele apontou na sua área. Acabou também?
  Melhore testes e acabamento das suas peças. **Parado nunca.**
- 🟡 no painel (alguém sem notícia há 20+ min) = o vigia cutuca. Não é motivo pra você parar.

---

## 👥 Quem faz o quê e as FILAS

Cada um só edita os próprios arquivos. Arquivo listado em `arquivos` de outro no painel = **não toque**.

### 🎨 Cursor: a cara do app
Arquivos: `caixa_home.py`, `caixa_busca_ui.py`, `caixa_tema.py`, `test_caixa_home.py`, `test_caixa_busca_ui.py`
- **F1**: `caixa_tema.py`, o visual novo. Paleta viva (base escura `#11131a` + `#7c5cff`, mas com cor por
  categoria), tipografia, cartão grande e pequeno. Algo que não pareça "formulário".
- **F2**: `caixa_home.py`, a tela Hoje. `class TelaHoje(QWidget)` recebe a lista de `sensores_core.ler_tudo()`
  e desenha os cartões, com botão de ação e atualização a cada 60 s numa thread (nunca trava a janela).
- **F3**: `caixa_busca_ui.py`, a barra. `class BarraBusca(QWidget)` com campo, lista de respostas embaixo,
  setas/Enter/Esc, e sinal `abrir_ferramenta(str chave)`. Responde enquanto digita (com debounce de 150 ms).
- **F4**: animações leves, estado vazio e de carregando, ajuste a 1366×768 e a 4K.
- **F5**: o que o Grok apontar no `CRITICA.md` sobre visual.
- **F6** (CRITICA F3, ALTA): fonte do valor no card da barra que desenhe `.` `,` e `R$` (Q10 saiu `1 030 30`);
  **Enter não abre ferramenta** quando já tem resposta na lista (só com a ferramenta selecionada de propósito);
  card mostra o `detalhe` da conta. Teste: Q10 e Q56 na tela.
- **F7**: sensores da Hoje com altura de verdade (nada de faixa de 60 px). O `caixa.pyw` já põe a Hoje numa
  rolagem e a janela agora cabe em 1366×768 (mín. 664×256) — ajuste o `TelaHoje` pra 1366×768 e 1920×1080
  mostrarem os GB livres e os 4 sensores sem rolar. Botão "Todas as ferramentas" com contraste.
- **F8**: atalho global **Ctrl+Espaço** + Caixa na bandeja (fechar = minimizar pra bandeja). Arquivo novo seu:
  `caixa_bandeja.py` com `class Bandeja` e `registrar_atalho(janela)`; o Claude liga no `caixa.pyw`.
- **F9**: botões da Hoje que **resolvem de verdade**: Disco → abre Faxina já no C:; Downloads → Organizador já na
  pasta Downloads; Prints → Print Anotador/OCR com o último print carregado; Pudim → abre o Pudim. Passe a pasta/arquivo
  por argumento (`--pasta`, `--arquivo`) só se a ferramenta já aceitar; senão `--pedir claude` com a lista.
- **F10**: destaque da Hoje ordenado pelo **uso real** (`cfg["uses"]` do caixa.pyw) com os 15 do Grok como ponto de
  partida; mostrar no máx. 8. Teste offscreen a 1366×768 e 3840×2160 (300% DPI).
- **F12** (bug real, achado em 10/11): fechar a janela com uma QThread rodando derruba o app (0xC0000409) e a Caixa mostra
  "a ferramenta fechou". A Faxina já foi corrigida (`closeEvent` → `stop()` + `wait(5000)`, ver `faxina-disco/faxina.pyw`).
  Faça o mesmo nas que têm `(QThread)` sem `closeEvent`: cabecalhos-seguranca, certificado-ssl, cliente-api, compactador,
  comparar-pastas, conversor-av, conversor-imagens, extrator-texto, gravador-voz, kit-pdf, limpa-metadados, metronomo,
  recupera-arquivos, rede, scanner-rede, visualizador-planilhas. Teste: abrir, iniciar a tarefa, fechar → sem crash.

### 🧠 Antigravity: os motores
Arquivos: `respostas_core.py`, `adp_essenciais.py`, `sensores_core.py`, `test_respostas.py`, `test_sensores.py`
- **F1**: `respostas_core.responder()` (o motor que carrega os adaptadores de `adp_indice.MODULOS`) e
  `adp_essenciais.py` com as 20 calculadoras mais comuns (porcentagem, troco, IPVA,
  juros, conversão de unidades, dias úteis, regra de 3, rendimento de tinta…) chamando os `_core.py`
  existentes. Entende número com vírgula, "mil", "R$" e "reais".
- **F2**: fazer o `test_respostas.py` passar em **50 das 60** perguntas do `PERGUNTAS.md` do Grok
  (se ainda não existir, use as suas e troque depois).
- **F3**: busca de reserva. Se não entender a frase, devolve as 5 ferramentas mais parecidas usando
  `catalogo.json` + `AJUDA.json`.
- **F4**: `sensores_core.ler_tudo()` para disco, Downloads e prints recentes (pasta Capturas de Tela),
  com cache e menos de 1 s.
- **F5**: sensores de vencimentos (dados salvos de garantias, remédios, contas fixas e assinaturas),
  área de transferência e Pudim (`%LOCALAPPDATA%\Programs\IPTV Player\player_config.json`, só leitura).
- **F6** (CRITICA F3): limpar a 2ª/3ª carta. Nada de resposta tautológica (`1 mes = 1 mes`) e **nenhum float cru**
  (`37.199999999999996`): formate todo número de `resposta`/`detalhe` em pt-BR num lugar só do `respostas_core`
  (pós-processamento), assim as 353 adaptações do Grok Build ganham de graça. Teste com Q10 e Q56.
- **F7**: ranking — carta com confiança < 0,35 não aparece se a 1ª tiver ≥ 0,8; no máximo 3 cartas.
- **F8**: lote 2 de perguntas (`PERGUNTAS.md` Q61–Q120, o Grok escreve): ≥ 50 de 60 passando.
- **F9**: em modo código o motor não pode depender de `staged/` (se faltar `<px>_core`, ache a pasta irmã pela
  chave do `catalogo.json`). Teste: renomeie `staged` num teste temporário e o IPVA continua respondendo.

### 🔌 Grok Build (agente de terminal): liga as 750 calculadoras na barra
Arquivos: `adp_indice.py` e `adp_<grupo>.py` (exceto `adp_essenciais.py`), `test_adp_<grupo>.py`.
O Antigravity faz o motor e as 20 mais comuns. **O Grok Build faz o resto**, para que as 750 que já
existem respondam na barra sem abrir janela. Cada grupo fica num arquivo próprio, então ninguém pisa no outro.
- **F1**: `adp_financas.py` com as calculadoras de 💰 Finanças & Trabalho (CLT, rescisão, férias, 13º,
  hora extra, juros, financiamento…). Leia o `_core.py` de cada uma e **chame a função real**, sem recalcular.
- **F2**: `adp_casa.py` (🏠 Casa, Pet & Pessoal).
- **F3**: `adp_ciencia.py` (🔬 Ciência & Engenharia) e `adp_unidades.py` (conversões).
- **F4**: `adp_dev.py` (💻 Dev & Dados: base64, hash, uuid, regex, subrede, cron…).
- **F5**: o resto das categorias, uma por arquivo. Depois, as falhas que o Grok marcar no `PERGUNTAS.md`.
- Não cria ferramenta nova, não edita `_core.py` de ninguém (bug no core? `--pedir claude`).
- **F6**: terminar `adp_outras.py` (estava em andamento, arquivo ainda não existe) + entrar em `adp_indice.MODULOS`.
- **F7**: `python catalogo.py` + `adp_indice` → gere `COBERTURA.md`: quais das 750 chaves NÃO têm adaptador.
  Ligue primeiro as que estão nos 15 destaques do Grok (F2) e as de 💰/🏠 sem adaptador.
- **F8** (enxuto): só os grupos 💰 `adp_financas` e 🏠 `adp_casa` — 3 jeitos de perguntar nas **20 chaves mais
  usadas** de cada (não em todas). Depois: as falhas que o Grok marcar no lote 2 do `PERGUNTAS.md`. Fila acabou = PARE e
  anuncie `--feito`; não invente tarefa.
- 💸 **Economia de tokens (Grok Build):** `/new` (sessão nova) a cada tarefa F terminada; nada de `grep` em todos os
  `adp_*.py` nem `read_file` de arquivo inteiro — leia só o trecho (offset/limit); use `catalogo.py --check` e
  `COBERTURA.md` em vez de inventariar de novo.
- ⛔ **F8 acabou em finanças + casa.** Ciência/unidades/dev ficam como estão. Agora: **pare** e espere o lote 2 do
  `PERGUNTAS.md` (Q61–Q120); quando sair, conserte só as falhas da sua área.

### 🧐 Grok Bot: crítico e testador (não constrói app)
Arquivos: `PERGUNTAS.md`, `CRITICA.md`
- **F1**: `PERGUNTAS.md`, 60 frases do jeito que o Caio escreveria (informal, abreviado, com erro de digitação),
  cada uma com a **resposta certa calculada à mão**. Elas viram os testes da barra.
- **F2**: das 750 ferramentas (`CATALOGO.md`), escolha as **15 que o Caio usaria de verdade** e diga por quê.
  Elas vão para o destaque da tela Hoje.
- **F3**: assim que sair um `.exe` novo, use a Caixa como o Caio e escreva no `CRITICA.md`:
  o que é inútil, confuso ou quebrado, com passo a passo. Seja duro.
- **F4**: rode as 60 perguntas na barra e marque quais falharam (vira pedido pro Antigravity).
- Se não conseguir editar arquivos, mande o texto para o Caio colar.
- **F5**: `PERGUNTAS.md` lote 2 (Q61–Q120): coisas do dia a dia do Caio que ainda não testamos (mercado, conta de
  luz, combustível, parcelas no cartão, Pix, horas trabalhadas, receita pra mais pessoas, datas). Resposta à mão.
- **F6**: quando sair `Caixa.exe` **1.5.1** (FileVersion preenchido), refaça o F3: janela abre na frente, cabe
  em 1366×768, foco na barra, aba Todas troca a tela, ⚙️ no lugar de boot/Menu Iniciar. Atualize `CRITICA.md`.
- **F7**: teste a Hoje de verdade: cada botão de cartão faz o que diz? (Disco → liberar, Downloads → arrumar,
  Prints → OCR/anotar, Pudim → abre). Duro, com passo a passo.

### 🔌 Grok CLI também é o INTEGRADOR e faz o BUILD (decisão do Caio, 2026-11-10: "Claude faz menos, delega mais")
Arquivos que passam a ser dele: `caixa.pyw` (só listas `BUILTIN`/`FERRAMENTAS_COM_ARGS`/`APP_VERSION`), `build_suite.py`
(só `TOOLS`/`COLLECT_ALL`), `instalador.iss` (versão), `EVOLUCAO.md`, `CATALOGO.md`/`catalogo.json`.
Checklist de integração (ferramenta nova ou `--feito` que pede "integrar"):
1. Revisar: `py_compile`, rodar o `test_<px>.py` da ferramenta, `git status` limpo na pasta dela (commit se faltar).
2. Tupla no FIM do `BUILTIN` + entrada no `TOOLS`; `python catalogo.py` (senão a barra não acha).
3. `python build_suite.py --stage-only` + `stagedpp.py --selftest` (tem que dar `OK: N`) + testes da Caixa
   (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -p no:cacheprovider test_respostas.py test_sensores.py test_adp_*.py test_caixa_*.py`).
Checklist de versão (quando juntar 2+ entregas OU tiver bug corrigido que o Caio vê, **no máx. 1 build a cada 2 h**,
e NUNCA em modo economia 🟡/🔴):
4. Subir `APP_VERSION` (caixa.pyw) + `AppVer` (instalador.iss) juntos; uma linha nova no topo do `EVOLUCAO.md`
   (`- **vX.Y.Z** · DD/MM · N ferramentas · o que o Caio ganhou`, em linguagem dele).
5. `python build_suite.py` **rodando de dentro de caixa-ferramentas** (nunca com shell parado em `staged\`).
6. Fechar a Caixa (`Get-Process Caixa | % CloseMainWindow`), `robocopy dist\Caixa %LOCALAPPDATA%\Programs\CaixaFerramentas /MIR`,
   `Caixa.exe --selftest` = `OK: N`, conferir FileVersion. Commit local (sem push).
7. `--feito "vX.Y.Z instalado: ..."` e `--pedir grok` pro Cocaino retestar o que mudou.

### 🔁 TROCA (Caio, 2026-11-10): Cocaino em RESERVA, Antigravity vira o testador/crítico
O Cocaino (SuperGrok) está perto do limite. Até segunda ordem (`agentes_pausados.json`):
- **Cocaino**: não recebe tarefa nem empurrão. Pedidos `--pedir grok` são entregues ao **Antigravity**.
- **Antigravity** (Gemini, mais cota): faz TUDO que era do Cocaino — testar cada versão nova, escrever o CRITICA.md,
  PERGUNTAS.md, aprovar as filas (escolher Propostas e pôr no quadro/RUMO) — além do motor da barra.
  Como testar sem ver a tela: scripts do Cocaino em `C:/Users/caion/fiscal-fabrica/` (`uia_teste.ps1`,
  `grok_f3_run_buscas.ps1`, PrintWindow) + abrir a Caixa com `Caixa.exe --teste` e `$env:CAIXA_TESTE='1'`.
  Mesmas regras de teste abaixo (máx. 3 janelas, fechar tudo que abriu).
Pra desfazer: apagar `agentes_pausados.json`.

### 🧐 Cocaino: regra de teste (o Caio reclamou: "abriu 500 coisas e não fechou")
- No máximo **3 janelas de teste abertas ao mesmo tempo**. Abriu, testou, **fechou na hora** (pelo PID que você abriu).
- Abra a Caixa SEMPRE assim: `Caixa.exe --teste` (marca tudo que abrir; o carteiro fecha sozinho o que ficar aberto > 10 min).
- Sempre com `$env:CAIXA_TESTE='1'`. No fim de CADA tarefa: conferir que não sobrou nada seu aberto
  (Caixa.exe --tool, ferramentas, diálogos, Bloco de Notas, Explorer) e fechar. Nunca fechar o que o Caio abriu.

### 🧐 Cocaino: além de testar, APROVA as filas
Quando a fila de alguém acabar, o **Antigravity** propõe 3 tarefas novas no `CRITICA.md` (seção "Propostas"), o
Cocaino escolhe as úteis pro Caio e escreve no RUMO.md na fila de quem vai fazer, com `--pedir` pra avisar.

### 🧑‍🍳 Claude: árbitro (entra pouco, de propósito)
O Claude **não** integra, não builda e não mantém fila no dia a dia. Chame com `python painel.py <você> --pedir claude "..."`
só para: bug no core que trava todo mundo, decisão de rumo, conflito entre agentes, mudar carteiro/economia/painel/vigia.
Arquivos que continuam dele: `carteiro.py`, `economia.py`, `painel.py`, `painel_adesivo.pyw`, `tendencias.py`, `RUMO.md`.

## Contratos entre as peças (pra ninguém esperar ninguém)
- `respostas_core.responder(texto: str) -> list[dict]`, com dicts
  `{"titulo", "resposta", "detalhe", "chave_ferramenta", "confianca"}` (confiança de 0 a 1). Lista vazia = não entendeu.
- `sensores_core.ler_tudo() -> list[dict]`, com dicts
  `{"id", "emoji", "titulo", "valor", "detalhe", "acao": {"rotulo", "chave_ferramenta" ou "comando"}}`.
  Só sensor com dado real, em menos de 1 s.
- **Adaptadores** (`adp_*.py`): cada um expõe `ADAPTADORES = [ {"chave": "<chave da ferramenta>",
  "palavras": ["ipva", "imposto carro"], "extrair": f(texto) -> dict | None, "calcular": f(params) -> dict} ]`,
  em que `calcular` devolve `{"resposta", "detalhe"}`. `adp_indice.py` tem `MODULOS = ["adp_essenciais", "adp_financas", ...]`
  (lista explícita, porque o build achata tudo numa pasta só). `respostas_core` importa os módulos de
  `MODULOS`, roda `extrair` e chama `calcular` no melhor. Utilitários de pt-BR (`numero_br("1.234,50")`, "mil",
  "R$", datas) ficam no `respostas_core` para todos usarem. Enquanto o `respostas_core` não existir, o Grok Build
  testa os adaptadores dele direto (o contrato é este).
- Stub só dentro de `test_*.py`, **nunca** na versão buildada.

## ✅ Pronto = o Caio abre, entende sem explicação e usa
A barra responde as perguntas do `PERGUNTAS.md`, os cartões mostram dados reais do PC.
Continuam valendo as regras de ouro do `AGENTS.md`: zero placeholder, `def main()`, pt-BR com acento.

## 🚫 Proibido
- Criar ferramenta/pasta nova de calculadora.
- Editar arquivo de outro agente ou o `painel/*.json` de outro à mão.
- Dado inventado ou exemplo fixo fingindo ser real.
- Ficar parado esperando alguém, ou perguntar ao Caio "posso continuar?".
