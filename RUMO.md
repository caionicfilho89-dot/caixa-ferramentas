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

### 🧑‍🍳 Claude: arquiteto e integrador
Arquivos: `caixa.pyw`, `build_suite.py`, `RUMO.md`, `painel.py` e os demais `.md`
- Liga a tela Hoje e a barra no `caixa.pyw` assim que aparecer `--feito` do Cursor ou do Antigravity
  no painel. Revisa, roda testes, builda o `.exe`, atualiza `%LOCALAPPDATA%\Programs\CaixaFerramentas`
  e commita. Mantém as filas deste arquivo com tarefas, para ninguém ficar sem o que fazer.
- 2026-11-10: janela cabe na tela (mín. 664×256, centraliza, abre na frente, foco na barra), Hoje em rolagem,
  aba Todas troca na hora, ⚙️ junta boot/Menu Iniciar, trava de janela duplicada (2,5 s), FileVersion no exe; v1.5.1.

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
