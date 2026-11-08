# 🧭 AGENTS.md — Central de Objetivo e Especificações da Caixa de Ferramentas

> **Este é o arquivo MESTRE.** Todo agente (Claude, Gemini, Antigravity, Codex, Kilo…) lê ISTO primeiro.
> `CLAUDE.md`, `GEMINI.md`, `INSTRUCTIONS_AGENT.md` e `BACKLOG.md` são complementares — em caso de
> conflito, **vale o que está aqui**. Ao fim de cada sessão, atualize a seção **📌 Estado atual** e o
> **📝 Log de atualizações** no final.

Fale com o Caio em **pt-BR informal**, respostas diretas e sem enrolação.

---

## 🎯 Objetivo

Construir a **maior caixa de ferramentas do mundo** — meta declarada pelo Caio:
**"a caixa ter um milhão de funções"**.

### ⚠️ Regras de Ouro Inegociáveis (decisão do Caio em 2026-11-08)

1. **ZERO PLACEHOLDERS NA VERSÃO FINAL BUILDADA:**
   - **Proibido** qualquer botão "em breve", `QMessageBox("será implementado")`, `TODO`, `pass`, valor
     fixo fingindo cálculo, scraper ingênuo que nunca funciona, ou script `.pyw` sem `def main()`.
   - **Tudo tem que funcionar de forma 100% REAL.** Antes de dar qualquer ferramenta ou build como pronta,
     teste o fluxo real (abrir janela, clicar nas ações principais, salvar/carregar, e verificar se existe
     `def main()` chamável pelo `Caixa.exe --tool <chave>`).
2. **INTERNET E RECURSOS EXTERNOS SÃO LIVRES E BEM-VINDOS:**
   - **NÃO existe obrigação de ser apenas offline.** Se uma ferramenta ficar mais útil ou precisar de
     internet (APIs, scraping real com cabeçalhos/JSON-LD, rede local Wi-Fi, consultas DNS/SSL/HTTP,
     cotações, downloads, etc.) ou elevação UAC do Windows (como editar o arquivo `hosts`), **faça o
     que for preciso para funcionar de verdade**. Não trave ideias por restrição artificial de offline.
3. **Crescer com FERRAMENTAS NOVAS:**
   - Cada ferramenta nova = um **app próprio e completo**, com seu **cartão na grade da Caixa**
     (`BUILTIN` em `caixa.pyw` + `TOOLS` em `build_suite.py`) e sua pasta irmã em `C:\Users\caion\<pasta>`.
   - **Proibido** repetir ferramenta já existente com outro nome ou repetir função entre ferramentas.
4. **NÃO inflar ferramentas antigas:**
   - O **🔪 Canivete Suíço fica CONGELADO em 800 funções** (apenas manutenção/correção se necessário).
   - "**prossiga**" do Caio = próxima rodada de **ferramentas novas completas**.

### Antes de criar qualquer ferramenta — checagem anti-repetição (obrigatória)
- Ler `BUILTIN` em `caixa.pyw` (nome + descrição de todas as ferramentas).
- Buscar a ideia nas pastas existentes (`C:\Users\caion\*\*.py*`).
- Conferir se a função já não existe no Canivete (`C:\Users\caion\canivete\cn_registry*.py`).

---

## 📌 Estado atual (ATUALIZE ao fim de cada sessão)

| Item | Valor |
|---|---|
| Ferramentas na grade | **144** (Rodadas 1–24 + Canivete Suíço) |
| Funções no Canivete | **800** em 81 categorias (congelado) |
| Outras ferramentas multi-função | Ferramentas BR (74) · Ferramentas Dev (31) · Kit Hacker (22) |
| Ferramentas consertadas em 2026-11-08 | **Monitor de Preços**, **Autenticador 2FA**, **Bloqueador de Sites**, **Detector de Duplicatas**, **Gerador de Dados**, **Analisador de Espaço**, **Quadro Branco** (todas agora têm `def main()` e implementação real completa) |
| Rodada 14 (integrada em 2026-11-08) | `scanner-documentos` (`scn_`), `compartilhar-rede` (`lan_`), `editor-legendas` (`lg_`), `teste-hardware` (`th_`), `mapa-mental` (`mm_`) |
| Rodada 15 (integrada em 2026-11-08) | `quadro-kanban` (`kb_`), `auditoria-pc` (`aud_`), `inspetor-executavel` (`dk_`), `estudios-gif` (`gif_`), `cofre-snippets` (`snip_`), `leitor-rss` (`rss_`) |
| Rodada 16 (integrada em 2026-11-08) | `gerenciador-servicos` (`svc_`), `analisador-wifi` (`wfi_`), `auditor-seo` (`seo_`), `corte-chapas` (`ccp_`), `comparador-dados` (`dfx_`), `laboratorio-audio` (`syn_`) |
| Rodada 17 (integrada em 2026-11-08) | `gravador-macros` (`mcr_`), `inspetor-http` (`prx_`), `planetario` (`ast_`), `codigo-barras` (`bar_`), `laboratorio-quimica` (`chm_`), `comparador-credito` (`crd_`) |
| Rodada 18 (integrada em 2026-11-08) | `scanner-rede` (`lsc_`), `simulador-circuitos` (`elt_`), `laboratorio-dna` (`dna_`), `analisador-logs` (`lga_`), `estudio-rotas` (`gpx_`), `calculadora-matrizes` (`mtx_`) |
| Rodada 19 (integrada em 2026-11-08) | `gerenciador-firewall` (`fwl_`), `painel-docker` (`dck_`), `laboratorio-estatistica` (`stt_`), `ficha-medica` (`med_`), `estudio-midi` (`mid_`), `agendador-tarefas` (`sch_`) |
| Rodada 20 (integrada em 2026-11-08) | `horta-jardim` (`agr_`), `inspetor-processos` (`prc_`), `estudio-svg` (`svg_`), `radio-morse` (`mrs_`), `cubagem-cargas` (`cub_`), `gerador-ssh` (`ssk_`) |
| Rodada 21 (integrada em 2026-11-08) | `leitor-nfe` (`nfe_`), `estudio-xadrez` (`chz_`), `calculadora-subrede` (`ipm_`), `simulador-fisica` (`fsc_`), `estudio-markdown` (`mdx_`), `gerador-ofx` (`ofx_`) |
| Rodada 22 (integrada em 2026-11-08) | `gerador-ssl` (`gsl_`), `estudio-som` (`som_`), `simulador-optica` (`opt_`), `conversor-coordenadas` (`geo_`), `benchmark-pc` (`bmk_`), `calculadora-combinatoria` (`cmb_`) |
| Rodada 23 (integrada em 2026-11-08) | `estudio-cifras` (`cfr_`), `estudio-tipografia` (`tip_`), `inspetor-pcap` (`pcp_`), `estudio-cronometro` (`crn_`), `arvore-decisao` (`tre_`), `inspetor-regex` (`rgx_`) |
| Rodada 24 (integrada em 2026-11-08) | `estudio-grafos` (`grf_`) |
| Próximo passo | Continuação da Rodada 24 de **ferramentas novas** |

---

## 🏗️ Arquitetura (não quebrar)

- Raiz: `C:\Users\caion\caixa-ferramentas` (a Caixa). Cada ferramenta = **pasta irmã**
  `C:\Users\caion\<pasta>` (`BASE = os.path.dirname(HERE)`). **Nunca** criar ferramenta dentro de
  `caixa-ferramentas\`.
- GUI: `<px>_gui.pyw` (ou `<nome>.pyw`) · lógica em `<px>_core.py`.
- **Prefixo de módulo ÚNICO** por ferramenta (inclusive no arquivo `test_<px>.py`!): o `build_suite.py`
  achata todos os `.py` numa pasta só (`staged/`); se dois arquivos tiverem o mesmo nome (ex.: dois
  `test_pm.py`), o stage aborta com `COLISÃO`.
  - Prefixos já usados: `kh_ fd_ clt_ cu_ pb_ fa_ cg_ rc_ car_ hb_ sb_ dd_ gd_ as_ pm_ (e test_pmon)
    gs_ cm_ nc_ tg_ qb_ cv_ cn_ scn_ lan_ lg_ th_ mm_ kb_ aud_ dk_ gif_ snip_ rss_ svc_ wfi_ seo_ ccp_ dfx_ syn_ mcr_ prx_ ast_ bar_ chm_ crd_ lsc_ elt_ dna_ lga_ gpx_ mtx_ fwl_ dck_ stt_ med_ mid_ sch_ agr_ prc_ svg_ mrs_ cub_ ssk_ nfe_ chz_ ipm_ fsc_ mdx_ ofx_ gsl_ som_ opt_ geo_ bmk_ cmb_ cfr_ tip_ pcp_ crn_ tre_ rgx_ grf_` (+ os das rodadas 1–10). Sempre rode
    `python build_suite.py --stage-only` para validar.
- **OBRIGATÓRIO no rodapé de toda GUI `.pyw`:**
  ```python
  def main():
      app = QApplication.instance() or QApplication(sys.argv)
      app.setStyleSheet(QSS)
      win = MinhaJanela()
      win.show()
      sys.exit(app.exec())

  if __name__ == "__main__":
      main()
  ```
  *(Sem `def main()`, a ferramenta abre pelo `.pyw` solto mas **NÃO ABRE** dentro do `Caixa.exe`!)*
- Registro: tupla em `BUILTIN` (`caixa.pyw`) `(emoji, nome, descrição, pasta, script)` + entrada em
  `TOOLS` (`build_suite.py`).

## ✅ Definição de pronto (cada ferramenta nova)
1. Tudo funciona de verdade (online e/ou offline, UAC se editar arquivos de sistema, etc.). Zero placeholders.
2. UI pt-BR com acentos, tema escuro padrão (`#11131a` / `#7c5cff`).
3. Possui `def main()` e passa em `python build_suite.py --stage-only` + `python staged\app.py --selftest`.
4. Possui `test_<px>.py` testando a lógica real e smoke test offscreen da GUI.

## 🧨 Gotchas conhecidos
- **O terminal do agente roda numa sessão isolada da tela do Caio:** processos GUI iniciados pelo agente
  não aparecem na tela dele. Para o Caio abrir, passe o caminho (`C:\Users\caion\caixa-ferramentas\dist\Caixa\Caixa.exe`).
- **Sempre fechar `Caixa.exe` antes de rodar `build_suite.py`:** se houver processo `Caixa.exe` aberto,
  o PyInstaller falha ao sobrescrever `dist\Caixa`.
- **Atualizar tanto `dist\Caixa` quanto `%LOCALAPPDATA%\Programs\CaixaFerramentas`** quando fizer build,
  pois o atalho da Área de Trabalho aponta para `AppData\Local\Programs\CaixaFerramentas\Caixa.exe`.

---

## 📝 Log de atualizações (mais recente no topo)

- **2026-11-08 (Rodada 24 — 144 ferramentas):**
  - Criada, testada e integrada:
    1. **🕸️ Estúdio de Grafos & Dijkstra** (`estudio-grafos` / `grf_gui.pyw`): modelagem de topologia de redes, algoritmos de menor caminho ponderado (Dijkstra) com fila de prioridades e renderização de grafos com destaque visual do melhor percurso.
  - Todas as **144 ferramentas** passaram em `build_suite.py --stage-only` e `staged\app.py --selftest` (`OK: 144`).

- **2026-11-08 (Rodada 23 — 143 ferramentas):**
  - Criadas, testadas e integradas **6 ferramentas novas inéditas**:
    1. **📜 Estúdio de Cifras Clássicas** (`estudio-cifras` / `cfr_gui.pyw`): criptografia histórica com Cifra de César, Vigenère polialfabética, Atbash hebraica, transposição Rail Fence (Zigue-zague) e tabela comparativa de análise de frequência de letras em português.
    2. **✒️ Estúdio de Tipografia** (`estudio-tipografia` / `tip_gui.pyw`): dimensionamento de escalas modulares (Terça Maior, Razão Áurea, etc.), alturas de linha, pareamento tipográfico de fontes do sistema e gerador de CSS responsivo `:root`.
    3. **🦈 Inspetor de Pacotes PCAP** (`inspetor-pcap` / `pcp_gui.pyw`): leitor e analisador de capturas de rede do Wireshark / tcpdump com extração de cabeçalhos binários Ethernet, IPv4, portas TCP e UDP com amostra sintética integrada.
    4. **⏱️ Cronômetro & Relógio Xadrez** (`estudio-cronometro` / `crn_gui.pyw`): cronômetro esportivo de alta precisão com marcação de voltas acumuladas/deltas e Relógio de Xadrez oficial FIDE com acréscimo de tempo Fischer por lance.
    5. **🌳 Árvore de Decisão & ID3** (`arvore-decisao` / `tre_gui.pyw`): cálculo da Entropia de Shannon e Ganho de Informação para seleção da raiz e ramos da árvore no clássico algoritmo ID3 de Machine Learning.
    6. **🔍 Inspetor de Regex** (`inspetor-regex` / `rgx_gui.pyw`): testador e depurador de expressões regulares em tempo real com captura de grupos posicionais/nomeados, medição de latência em milissegundos e biblioteca de padrões prontos (CPF, Email, IP, URLs).
  - Todas as **143 ferramentas** passaram em `build_suite.py --stage-only` e `staged\app.py --selftest` (`OK: 143`).

- **2026-11-08 (Rodada 22 — 137 ferramentas):**
  - Criadas, testadas e integradas **6 ferramentas novas inéditas**:
    1. **🔒 Gerador de Certificados SSL** (`gerador-ssl` / `gsl_gui.pyw`): emissão de pares de certificados X.509 v3 autoassinados com extensões SAN (Subject Alternative Names para localhost/IPs) e chaves RSA 2048/4096-bit via OpenSSL.
    2. **🎵 Estúdio de Áudio & Ondas** (`estudio-som` / `som_gui.pyw`): sintetizador com osciladores de ondas Senoidais, Quadradas, Triangulares, Dente de Serra e Ruídos Acústicos (Branco/Rosa) com reprodução ao vivo e exportador WAV 44.1 kHz.
    3. **🔬 Laboratório de Óptica** (`simulador-optica` / `opt_gui.pyw`): cálculo e renderização da Lei de Snell-Descartes, reflexão total interna, ângulo crítico e Equação dos Fabricantes de Lentes (Lensmaker) para graus dióptricos.
    4. **🧭 Conversor de Coordenadas** (`conversor-coordenadas` / `geo_gui.pyw`): conversor geodésico WGS84 entre Graus Decimais (DD), Graus Minutos Segundos (GMS) e Projeção Plana UTM com Easting/Northing.
    5. **⚡ Benchmark de Memória & SSD** (`benchmark-pc` / `bmk_gui.pyw`): teste de taxa de transferência direta sequencial na memória RAM (GB/s) e gravação/leitura física em disco com sincronização direta `fsync()`.
    6. **🎲 Análise Combinatória & Loto** (`calculadora-combinatoria` / `cmb_gui.pyw`): combinatória completa (arranjos, combinações simples e com repetição, permutações reais) e cálculo de probabilidades de loterias (Mega-Sena, Lotofácil, Quina).
  - Todas as **137 ferramentas** passaram em `build_suite.py --stage-only` e `staged\app.py --selftest` (`OK: 137`).

- **2026-11-08 (Rodada 21 — 131 ferramentas):**
  - Criadas, testadas e integradas **6 ferramentas novas inéditas**:
    1. **📑 Leitor de NF-e XML** (`leitor-nfe` / `nfe_gui.pyw`): auditor tributário completo de XML de NF-e/NFC-e (vProd, vNF, ICMS, IPI, PIS, COFINS por item NCM/CFOP), gerador de CSV e validador de Chave de Acesso (44 dígitos com conferência Módulo 11).
    2. **♟️ Estúdio de Xadrez** (`estudio-xadrez` / `chz_gui.pyw`): tabuleiro vetorial interativo com dicas de lances válidos, cálculo de balanço material, importação/exportação FEN e reprodução de partidas imortais (Kasparov, Morphy, Fischer).
    3. **🌐 Arquiteto de Sub-redes** (`calculadora-subrede` / `ipm_gui.pyw`): calculadora de blocos CIDR IPv4/IPv6 (máscara binária, wildcard ACL, primeiro/último host útil) e alocador de sub-redes VLSM sem sobreposição para múltiplos departamentos.
    4. **🚀 Simulador de Física** (`simulador-fisica` / `fsc_gui.pyw`): cinemática e balística 2D vetorial com resistência do ar e gravidade de planetas (Terra, Marte, Lua, Júpiter), além de calculadora de mecânica orbital (velocidade circular e de escape).
    5. **📝 Estúdio Markdown & TeX** (`estudio-markdown` / `mdx_gui.pyw`): editor de notas técnicas com visualizador HTML/CSS ao vivo, suporte a tabelas GFM, fórmulas TeX KaTeX em bloco e inline, blocos de código e exportação para `.md` e `.html`.
    6. **🏦 Gerador de Extratos OFX** (`gerador-ofx` / `ofx_gui.pyw`): emulador de lançamentos bancários e gerador de arquivos OFX 1.02 válidos para testes de importação em ERPs, sistemas de contabilidade e plataformas financeiras.
  - Todas as **131 ferramentas** passaram em `build_suite.py --stage-only` e `staged\app.py --selftest` (`OK: 131`).

- **2026-11-08 (Rodada 20 — 125 ferramentas):**
  - Criadas, testadas e integradas **6 ferramentas novas inéditas**:
    1. **🌱 Horta & Adubação NPK** (`horta-jardim` / `agr_gui.pyw`): consultor de alelopatia/plantas companheiras, dimensionador de canteiros e espaçamento, e calculadora agronômica de adubação NPK (Ureia, MAP, KCl, NPK 10-10-10 e composto orgânico) + calagem dolomítica de pH.
    2. **🔍 Inspetor de Processos** (`inspetor-processos` / `prc_gui.pyw`): inspetor forense de processos em tempo real com rastreamento do Processo Pai (`PPID → PID`), linha de comando CLI completa, diretório de trabalho (`CWD`), processos filhos, arquivos abertos e botões para Congelar (`Suspend`), Retomar (`Resume`) e Encerrar (`Terminate`).
    3. **📐 Estúdio Vetorial SVG** (`estudio-svg` / `svg_gui.pyw`): gerador paramétrico de ícones, engrenagens, estrelas, polígonos e selos vetoriais SVG, minificador/otimizador XML com estatística de bytes economizados, renderizador vetorial ao vivo e exportador PNG/SVG.
    4. **📻 Rádio Amador & Morse** (`radio-morse` / `mrs_gui.pyw`): tradutor bidirecional Código Morse ↔ Texto, sintetizador CW de áudio real (44.1 kHz WAV com rampa anti-click e reprodução ao vivo), conversor fonético OTAN/ICAO e calculadora de antenas dipolo $\lambda/2$, vertical $\lambda/4$ e ROE (SWR).
    5. **📦 Cubagem & Cargas 3D** (`cubagem-cargas` / `cub_gui.pyw`): otimizador de paletização e encaixe 3D em paletes PBR/Euro, furgões, caminhões e containers 20'/40' HC com renderização isométrica 3D ao vivo, mais calculadora de Peso Cubado Taxável (Aéreo IATA 6000, Rodoviário ANTT 300 kg/m³ e Marítimo LCL W/M).
    6. **🔐 Chaves SSH & Config** (`gerador-ssh` / `ssk_gui.pyw`): gerador real de pares de chaves OpenSSH (`Ed25519` e `RSA-4096` via `ssh-keygen`), auditor de chaves públicas com cálculo de Fingerprint `SHA256`/`MD5` e arte ASCII *Drunken Bishop* (`RandomArt`), mais construtor visual de `~/.ssh/config`.
  - Todas as **125 ferramentas** passaram em `build_suite.py --stage-only` e `staged\app.py --selftest` (`OK: 125`).

- **2026-11-08 (Rodada 19 — 119 ferramentas):**
  - Criadas, testadas e integradas **6 ferramentas novas inéditas**:
    1. **🛡️ Gerenciador de Firewall** (`gerenciador-firewall` / `fwl_gui.pyw`): bloqueio de acesso à internet por executável `.exe` (regras de Entrada + Saída), abertura/bloqueio de portas TCP/UDP e listagem/remoção de regras do Windows Defender Firewall (`netsh advfirewall`) com elevação UAC automática.
    2. **🐳 Estúdio Docker** (`painel-docker` / `dck_gui.pyw`): gerador de stacks `docker-compose.yml` com volumes e healthchecks (Postgres, Redis, MySQL, RabbitMQ, Nginx), auditor de segurança de `Dockerfile` (CIS Benchmark) e painel de containers locais (`docker ps -a`).
    3. **📊 Laboratório de Estatística** (`laboratorio-estatistica` / `stt_gui.pyw`): estatística descritiva completa, quartis, intervalo de confiança de 95%, detecção de outliers (Tukey $1.5 \times \text{IQR}$), assimetria/curtose, regressão linear por mínimos quadrados ($r$ de Pearson, $R^2$) e gráficos de histograma + dispersão.
    4. **🩺 Prontuário & Exames** (`ficha-medica` / `med_gui.pyw`): avaliador clínico de exames de sangue frente aos valores de referência laboratoriais, calculadora de duração de estoque de medicamentos contínuos e exportador de Cartão Médico de Emergência em HTML.
    5. **🎹 Estúdio Piano Roll & MIDI** (`estudio-midi` / `mid_gui.pyw`): sequenciador musical interativo estilo Piano Roll, explorador de escalas/modos gregos, transposição de semitons, síntese de áudio WAV e gerador de arquivos binários Standard MIDI (`.mid` SMF Format 0).
    6. **🗓️ Simulador Cron & Agendador** (`agendador-tarefas` / `sch_gui.pyw`): tradutor de expressões Cron para português com simulação exata das próximas 10 datas/horários de disparo e integração real com o Agendador de Tarefas do Windows (`schtasks`).
  - Todas as **119 ferramentas** passaram em `build_suite.py --stage-only` e `staged\app.py --selftest` (`OK: 119`).

- **2026-11-08 (Rodada 18 — 113 ferramentas):**
  - Criadas, testadas e integradas **6 ferramentas novas inéditas**:
    1. **📡 Scanner de Rede Local** (`scanner-rede` / `lsc_gui.pyw`): descoberta de dispositivos vizinhos na LAN (`arp -a`), identificação de fabricante pelo endereço MAC (OUI), sonda multi-thread de portas TCP comuns (`22`, `80`, `443`, `445`, `3389`, `8080`) e exportação CSV.
    2. **⚡ Simulador de Circuitos** (`simulador-circuitos` / `elt_gui.pyw`): malhas de resistores em série/paralelo, divisor de tensão com efeito de carga, filtro RC Passa-Baixas/Passa-Altas com Diagrama de Bode logarítmico (`QPainter`) e calculadora do oscilador astável NE555.
    3. **🧬 Bioinformática & DNA** (`laboratorio-dna` / `dna_gui.pyw`): análise de sequências FASTA/DNA, conteúdo GC%, temperatura de anelamento ($T_m$), transcrição DNA→mRNA, tradução de códons para cadeia polipeptídica, mapa de enzimas de restrição e alinhamento global Needleman-Wunsch.
    4. **📈 Analisador de Logs SIEM** (`analisador-logs` / `lga_gui.pyw`): auditoria de logs Apache/Nginx/JSONL, detecção de ataques (SQL Injection, XSS, Path Traversal, scanners `.env`/`wp-login`) mesmo com URL-encoding e leitor ao vivo do Visualizador de Eventos do Windows (`wevtutil`).
    5. **🗺️ Estúdio de Rotas GPX** (`estudio-rotas` / `gpx_gui.pyw`): importador/exportador de trilhas `.GPX`, distância geodésica Haversine, ganho/perda de elevação acumulada (`D+`/`D-`), estimativa de tempo de trilha pela regra de Naismith e gráficos de traçado 2D + perfil altimétrico.
    6. **📐 Calculadora de Matrizes** (`calculadora-matrizes` / `mtx_gui.pyw`): determinante, matriz inversa $A^{-1}$, posto, traço, condicionamento, autovalores reais/complexos, produto matricial $A \times B$ e resolução de sistemas lineares $A\cdot x = b$ (LU e Mínimos Quadrados).
  - Todas as **113 ferramentas** passaram em `build_suite.py --stage-only` e `staged\app.py --selftest` (`OK: 113`).

- **2026-11-08 (Rodada 17 — 107 ferramentas):**
  - Criadas, testadas e integradas **6 ferramentas novas inéditas**:
    1. **⚡ Automação & Macros** (`gravador-macros` / `mcr_gui.pyw`): estúdio de automação de mouse e teclado via Win32 (`user32`), captura de coordenadas ao vivo com tecla `F8`, controle de velocidade/repetições, parada de emergência (`ESC`) e perfis JSON.
    2. **🌐 Receptor de Webhooks** (`inspetor-http` / `prx_gui.pyw`): servidor HTTP Mock multi-thread local, captura em tempo real de métodos/headers/query/body, simulação de status HTTP e latência, disparador de teste integrado e gerador de comando `cURL`.
    3. **🔭 Planetário & Efemérides** (`planetario` / `ast_gui.pyw`): radar polar 360° da abóbada celeste, cálculo orbital de nascer/meio-dia/pôr do Sol, fases e iluminação da Lua e altitude/azimute ao vivo de Mercúrio, Vênus, Marte, Júpiter e Saturno.
    4. **📦 Código de Barras 1D** (`codigo-barras` / `bar_gui.pyw`): gerador e validador industrial `EAN-13` (GS1 Brasil 789/790), `EAN-8`, `Code-128B` e `ITF-14` com cálculo automático de dígito verificador, gerador de lote sequencial e exportação PNG de alta nitidez.
    5. **🧪 Laboratório de Química** (`laboratorio-quimica` / `chm_gui.pyw`): parser recursivo de fórmulas químicas com parênteses e hidratos, cálculo de massa molar e % em massa por elemento, balanceador estequiométrico exato via eliminação Gauss-Jordan em frações e catálogo da Tabela Periódica.
    6. **🏦 Amortização & Consórcio** (`comparador-credito` / `crd_gui.pyw`): simulador de amortização extraordinária mensal (`SAC` e `PRICE`) revelando meses cortados e juros economizados, mais comparativo financeiro real entre Financiamento e Consórcio reajustado pelo INCC.
  - Todas as **107 ferramentas** passaram em `build_suite.py --stage-only` e `staged\app.py --selftest` (`OK: 107`).

- **2026-11-08 (Rodada 16 — Marco de 101 ferramentas!):**
  - Criadas, testadas e integradas **6 ferramentas novas inéditas**:
    1. **🔧 Gerenciador de Serviços** (`gerenciador-servicos` / `svc_gui.pyw`): auditoria de serviços do Windows (`psutil`), filtro de serviços de terceiros (não-Microsoft), inspeção de binários e controle (`start`/`stop`/`auto`/`demand`/`disabled`) via `sc.exe` com elevação UAC automática.
    2. **📡 Analisador de Wi-Fi** (`analisador-wifi` / `wfi_gui.pyw`): scanner de BSSIDs e espectro de canais 2.4/5 GHz (`netsh wlan`), recomendador automático do canal menos congestionado (1 vs 6 vs 11) e cofre de senhas Wi-Fi salvas no PC (`key=clear`) + payload QR Code.
    3. **🔍 Auditor de SEO & Links** (`auditor-seo` / `seo_gui.pyw`): auditoria técnica de páginas web (URL ao vivo ou HTML), pontuação 0–100, prévia Google SERP e OpenGraph, hierarquia `H1`–`H6`, detector de imagens sem `alt` e verificador HTTP (`HEAD`) de links quebrados.
    4. **📐 Corte de Chapas 2D** (`corte-chapas` / `ccp_gui.pyw`): otimizador de plano de corte guilhotina 2D (MDF, vidro, chapas metálicas) e barras lineares 1D com compensação de espessura de serra (`kerf`), mapa visual `QPainter` por chapa e exportação CSV.
    5. **🧬 Comparador de Configs** (`comparador-dados` / `dfx_gui.pyw`): diff estrutural semântico e tradutor bidirecional entre `JSON`, `CSV`, `INI` e `.env`, mais mascarador automático de segredos (`API_KEY`, `PASSWORD`, `TOKEN`).
    6. **🎛️ Laboratório de Áudio** (`laboratorio-audio` / `syn_gui.pyw`): sintetizador polifônico 44.1 kHz com envelope ADSR, gerador de acordes, batidas binaurais de foco/relaxamento (Delta, Theta, Alpha, Beta, Gamma), osciloscópio e analisador de espectro FFT em tempo real.
  - Todas as **101 ferramentas** passaram em `build_suite.py --stage-only` e `staged\app.py --selftest` (`OK: 101`).

- **2026-11-08 (Rodada 15 — 95 ferramentas):**
  - Criadas, testadas e integradas **6 ferramentas novas inéditas**:
    1. **📋 Quadro Kanban** (`quadro-kanban` / `kb_gui.pyw`): gestão ágil em colunas, limites WIP com alerta visual, Story Points, filtros por prioridade/tag e exportação CSV.
    2. **🛡️ Auditoria de Portas** (`auditoria-pc` / `aud_gui.pyw`): auditoria ao vivo de portas TCP/UDP abertas e conexões ativas (`psutil`), mapeando PID, nome/caminho do executável e nível de exposição (`0.0.0.0` vs loopback).
    3. **🔬 Inspetor de Executáveis** (`inspetor-executavel` / `dk_gui.pyw`): parser binário PE (`.exe`/`.dll`/`.sys`), tabela de seções, cálculo de entropia de Shannon por seção (detector de packers/UPX), hashes MD5/SHA1/SHA256, extrator de strings ASCII/UTF-16 e visualizador Hex.
    4. **🎞️ Estúdio de GIF & Sprites** (`estudios-gif` / `gif_gui.pyw`): criador e extrator de GIFs animados, efeito Boomerang, legenda sobreposta, gerador de Spritesheet e fatiador de grades.
    5. **🧩 Cofre de Snippets** (`cofre-snippets` / `snip_gui.pyw`): cofre parametrizado de comandos CLI, SQL, Git e Docker que detecta variáveis `{{nome:padrao}}` e gera formulário ao vivo pronto pra copiar.
    6. **📰 Leitor de Feeds RSS** (`leitor-rss` / `rss_gui.pyw`): agregador online de feeds RSS 2.0 e Atom XML com leitor limpo, busca e favoritos.
  - Todas as **95 ferramentas** passaram em `build_suite.py --stage-only` e `staged\app.py --selftest` (`OK: 95`).

- **2026-11-08 (Tarde)** — Descoberta e correção da causa raiz das ferramentas que não abriam ou tinham
  placeholder no `.exe`:
  1. 6 ferramentas das Rodadas 11–13 (`autenticador-2fa`, `site-blocker`, `duplicate-detector`,
     `dummy-data-generator`, `disk-analyzer`, `quadro-branco`) não tinham `def main()`, então clicando nelas
     no `Caixa.exe` dava `AttributeError`. Corrigidas todas + `selftest` agora exige `callable(m.main)`.
  2. **Autenticador 2FA (`fa_gui.pyw`)** estava com placeholder na GUI ("será implementada"): reescrito por
     completo integrando o cofre AES-256-GCM (`fa_core.py`), gerador TOTP/HOTP ao vivo, busca e import/export.
  3. **Monitor de Preços (`pm_core.py` / `pm_gui.pyw`)** reescrito com extrator real (JSON-LD Schema.org,
     OpenGraph, meta tags, seletores de e-commerce BR), cotação manual, alerta de meta e gráfico de evolução.
  4. **Bloqueador de Sites (`sb_core.py` / `sb_gui.pyw`)** reescrito com elevação UAC automática (`runas`),
     bloqueio de domínio + `www.`, pacotes de foco e `ipconfig /flushdns`.
  5. **Rodada 14 concluída (5 ferramentas novas reais):** Scanner de Documentos (`scn_`), Compartilhar na Rede
     (`lan_`), Editor de Legendas (`lg_`), Teste de Periféricos (`th_`) e Mapa Mental (`mm_`). Total: **89 ferramentas**.
  6. Regra atualizada pelo Caio: zero placeholders na build final e liberdade total para usar recursos online/sistema.


## Rodada 24 Concluída (149 Ferramentas Totais)
- **144. Estúdio de Grafos & Dijkstra (`estudio-grafos`, `grf_`)**: Modelagem de topologias de rede, algoritmo de Dijkstra com fila de prioridade e menor caminho ponderado.
- **145. Simulador de Portas Lógicas (`simulador-logica`, `lgc_`)**: Álgebra booleana, portas lógicas (AND, OR, NOT, NAND, NOR, XOR, XNOR), gerador de tabelas-verdade, mintermos/maxtermos e visualizador do Mapa de Karnaugh.
- **146. Analisador de Áudio & FFT (`analisador-audio-fft`, `fft_`)**: Transformada Rápida de Fourier (FFT Cooley-Tukey pura), detecção de frequência de pico e notas musicais, medição em dBFS, centroide espectral e analisador de harmônicos.
- **147. Validador de JSON Schema (`validador-json-schema`, `jsc_`)**: Validador Draft-07 sem dependências externas, verificação de tipos, required, pattern regex, enum, min/max, e gerador automático de esquema (inferência).
- **148. Calculadora de Engrenagens (`calculadora-engrenagens`, `grs_`)**: Engrenagens cilíndricas de dentes retos (módulo, diâmetro primitivo, distância entre centros, adendo/dedendo), cálculo de torque, RPM e trens redutores compostos multi-estágios.
- **149. Gerador de Sitemap & Robots (`gerador-sitemap`, `stm_`)**: Protocolo sitemaps.org XML, analisador/validador de integridade de tags de indexação e gerador de robots.txt com diretivas Allow/Disallow/Crawl-delay.


## Rodada 25 Concluída (155 Ferramentas Totais)
- **150. Simulador Gravitacional N-Corpos (`simulador-gravitacional-n-corpos`, `nbd_`)**: Mecânica celeste newtoniana com integrador simplético Velocity-Verlet, softening de Plummer, conservação de energia e órbitas periódicas clássicas.
- **151. Calculadora de Concreto Armado (`calculadora-concreto-armado`, `cnc_`)**: Dimensionamento à flexão simples de vigas retangulares segundo a NBR 6118 / Eurocode 2, cálculo de linha neutra x/d, armadura longitudinal As, estribos de cisalhamento e quantitativos.
- **152. Compressão de Huffman & Entropia (`estudio-compressao-huffman`, `huf_`)**: Codificador de árvores binárias de Huffman com min-heap, empacotamento em bytes reais, verificação de integridade sem perdas e cálculo de Entropia de Shannon H(X).
- **153. Laboratório de Autômatos Celulares (`simulador-automato-celular`, `cll_`)**: Conway's Game of Life 2D (B3/S23) com grade interativa e presets (Glider, Pulsar, LWSS), autômatos elementares de Stephen Wolfram 1D (Regras 0-255) e Formiga de Langton.
- **154. Analisador de Geo IP & Rede (`analisador-geo-ip`, `gip_`)**: Geolocalização de IP e ASN, DNS reverso (PTR), cálculo de distância geodésica pela fórmula de Haversine e estimativa de latência óptica mínima (RTT) em fibra de vidro.
- **155. Estatística & Inferência Bayesiana (`calculadora-estatistica-bayesiana`, `bys_`)**: Teorema de Bayes, paradoxo do falso positivo em testes de triagem médica / spam, cálculo de PPV, NPV, razões de verossimilhança e modelo conjugado Beta-Binomial.
