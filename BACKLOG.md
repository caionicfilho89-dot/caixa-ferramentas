# 🧰 Backlog da Caixa de Ferramentas

Meta: a maior caixa de ferramentas offline do mundo. As rodadas continuam agrupadas em 5 ferramentas,
mas o Gemini CLI via Kilo Free implementa uma por conversa, em sequência e com checkpoints em arquivo;
sem subagentes ou varredura de todas as pastas. O Claude pode revisar e integrar a rodada concluída.

Regras de toda ferramenta: offline sempre que possível, UI pt-BR, tema escuro padrão,
módulos auxiliares com prefixo único, testada (py_compile + lógica + GUI offscreen),
nada que sirva pra golpe/ataque a terceiros.

## ✅ Na Caixa
1–17 (kit-pdf … gps-falso) · 18 Ferramentas BR (74 funções) · 19–23 Rodada 1 (v1.4.0) · 24–28 Rodada 2 · 29–33 Rodada 3 · 34–38 Rodada 4 · 39–43 Rodada 5 · 44–48 Rodada 6 · 49–53 Rodada 7 · 54–58 Rodada 8 · 59–63 Rodada 9 · 64–68 Rodada 10 · 69–73 Rodada 11 · 74–78 Rodada 12 · 79–83 Rodada 13 = 83 ferramentas no código

## ✅ Rodada 1 (integrada na v1.4.0)
- 🧰 Kit do Hacker — codificar/decodificar, hash, JWT, timestamp
- 📱 Ferramentas Dev — JSON/XML/SQL, regex, diff, cron
- 💰 Calculadora CLT — líquido, férias, 13º, rescisão (tabelas 2026)
- 📏 Conversor de Unidades e Moedas
- 💸 Pix & Boleto — gerar Pix pra receber, ler Pix, conferir boleto

## ✅ Rodada 2 — dia a dia (integrada)
- 💵 Finanças pessoais — juros compostos, financiamento SAC/Price, CDB x poupança x Tesouro, dividir conta
- ⏱️ Tempo — pomodoro, cronômetro, timer, alarme, desligar o PC agendado
- 📝 Notas Markdown — editor com prévia, pastas, busca
- ✅ Tarefas e lembretes — to-do com prazo + aviso na bandeja
- 📅 Calendário BR — feriados nacionais, dias úteis entre datas, contagem regressiva

## ✅ Rodada 3 — PC (integrada)
- 📊 Monitor do sistema — CPU/RAM/disco/rede ao vivo, processos, temperatura se der
- 💽 Info do PC — hardware, Windows, bateria (saúde), drivers
- 🚀 Inicialização — ver/desativar programas que abrem com o Windows
- 🗜️ Compactador — ZIP criar/extrair (com senha), ver conteúdo
- 🔐 Criptografar arquivos — trancar/destrancar arquivo com senha (AES)

## ✅ Rodada 4 — mídia (integrada)
- 🖼️ Editor de imagem rápido — cortar, redimensionar, girar, marca d'água, filtros
- 🎙️ Gravador de voz — microfone → MP3/WAV
- 🎨 Paletas de cores — gerar paleta harmônica, extrair cores de uma foto
- 📷 Webcam — espelho, foto, gravação curta
- 🔤 Visualizador de fontes — ver todas as fontes instaladas com texto de exemplo

## ✅ Rodada 5 — rede e diversão (integrada)
- 🌐 Rede — meu IP, ping, DNS, traceroute, Wi-Fi conectado, teste de velocidade
- 🎲 Sorteios — amigo secreto, dividir times, roleta, cara ou coroa, dados
- 🏥 Saúde — IMC, água por dia, calorias, sono
- 🃏 Flashcards — estudo com repetição espaçada (SM-2) [substituiu o expansor de texto]
- 🧮 Calculadora científica + gráfico de funções

## ✅ Rodada 6 — escritório (integrada)
- 📈 Visualizador de Planilhas — abre CSV/XLSX, filtra, ordena, soma, gráfico, exporta
- 🧾 Orçamentos e Recibos — pra MEI/autônomo: cadastro de clientes/itens, gera PDF com numeração
- 📇 Contatos — agenda offline, importa/exporta vCard e CSV, busca, aniversários
- 📖 Leitor de E-books — EPUB/TXT, marcadores, tamanho de fonte, modo noturno
- 📂 Organizador de Downloads — regras por tipo/data, MOVE (nunca apaga), desfazer

## ✅ Rodada 7 — dev e segurança defensiva (integrada)
- 🔌 Cliente de API — requisições HTTP estilo Postman (coleções, histórico, JSON bonito)
- 🗄️ Visualizador SQLite — abre .db, navega tabelas, roda SELECT, exporta CSV
- 🛡️ Checar cabeçalhos de segurança do SEU site — HSTS/CSP/X-Frame etc. com explicação
- 🔒 Certificado SSL — ver validade/emissor/cadeia de um domínio, avisar vencimento
- 🐍 Caderno Python — rodar snippets locais com saída, salvar trechos

## ✅ Rodada 8 — aprender e se divertir (integrada)
- ⌨️ Treino de digitação — PPM, precisão, textos em pt-BR
- 🧩 Sudoku — gerador com níveis, dicas, notas
- 🎵 Metrônomo e afinador — BPM com batida; afinador pelo microfone
- 🌍 Relógio mundial — fusos, conversor de horário, "melhor horário pra reunião"
- 🗺️ Quiz de Geografia — bandeiras (desenhadas), capitais, estados do Brasil

## ✅ Rodada 9 — Windows turbinado (integrada)
- 🪟 Janelas — deixar qualquer janela sempre no topo, transparência, centralizar, layouts lado a lado
- 🔊 Volume por App — controlar o volume de cada programa separado, perfis
- 📁 Comparar Pastas — diferenças entre duas pastas (novos/alterados/faltando), copiar com prévia
- ⚙️ Variáveis de Ambiente — ver/editar PATH e variáveis do usuário com backup
- 🖼️ Galeria de Fotos — visualizador rápido de pasta, slideshow, EXIF, girar sem perda

## ✅ Rodada 10 — criadores e escrita (integrada)
- 📄 Currículo em PDF — modelos bonitos, preenche e exporta
- 🏷️ Etiquetas em lote — etiquetas/QR/códigos de barras pra imprimir em folha A4
- ✍️ Analisador de Texto — legibilidade, palavras repetidas, tempo de leitura, frases longas
- 🔊 Texto para Fala — lê texto em voz alta com as vozes do Windows, salva WAV
- 🎵 Player de Música — toca a pasta de músicas, playlists, equalizador simples

## ✅ Rodada 11 — vida organizada (integrada)
- 🔐 Autenticador 2FA — códigos TOTP das SUAS contas, guardados criptografados, importa QR
- 💰 Controle de Gastos — lançamentos, categorias, orçamento do mês, gráficos, importa CSV do banco
- 🍳 Receitas — caderno de receitas, ajustar porções, lista de compras
- 🚗 Controle do Carro — abastecimentos, consumo km/l, manutenções e lembretes
- 🏁 Hábitos — checklist diário, sequências, calendário de progresso

## ✅ Rodada 12 — criar e compartilhar (parcial — 5/5 integradas)
- 🚫 Bloqueador de Sites — bloqueia sites editando o arquivo hosts do Windows
- 🔍 Detector de Duplicatas — escaneia pastas e deleta arquivos duplicados (MD5)
- 🎲 Gerador de Dados — gera dados falsos (nomes/emails) em CSV/JSON
- 💾 Analisador de Espaço — analisa e lista o tamanho de arquivos e pastas
- 💹 Monitor de Preços — monitora preços de produtos em sites (offline)

## ✅ Rodada 13 — vida digital (integrada)
- 🔑 Gerador de Senhas — senhas seguras com avaliação de força
- 💱 Conversor de Moedas — BRL, USD, EUR, BTC e ETH offline
- 📝 Notas Criptografadas — cofre de notas com AES-256-GCM
- 🍽️ Gorjeta e Divisão — calcule gorjeta e divida a conta
- 🖌️ Quadro Branco — desenho livre, formas, texto, exportar PNG/PDF

## ✅ Rodada 29 — nichos do dia a dia (integrada — ~208 ferramentas com paralelas)
- 🐾 Dose de Ração & Pet (`pet_`) — RER/MER de cão/gato, gramas/dia, água, idade humana
- 💇 Cronograma Capilar & Oxidante (`cab_`) — agenda H/N/R + volumes↔% e diluição de oxigenada
- 🧳 Divisor de Despesas em Grupo (`rct_`) — racha conta: saldos + menor nº de transferências

## ✅ Rodada 28 — jogos, mar e maternidade (integrada — 185 ferramentas no código)
- 🎲 Laboratório de Dados RPG (`rpg_`) — distribuição exata NdM+K, P(≥alvo), vantagem/desvantagem, histograma
- 🧭 Navegação & Rumo (`nav_`) — ortodrômica/loxodrômica, rumo, ponto de chegada, ETA em nós
- 🤰 Calculadora Gestacional (`gst_`) — DPP Naegele, semanas, trimestre, concepção; pela DUM ou ultrassom
- (sessão paralela entre a 27 e a 28: `uni_`, `mtc_`, `qtn_`, `phn_`)

## ✅ Rodada 27 — esporte, rádio e finanças (integrada — 178 ferramentas no código)
- 🏃 Ritmo & Corrida (`pac_`) — ritmo↔velocidade, tempo de prova, splits, Riegel, VO2max, zonas de FC
- 📡 Calculadora RF & dBm (`rfc_`) — dBm/mW/W, somar potências, freq↔λ, FSPL, link budget, VSWR
- ⚖️ Juros de Mora & Multa (`jmr_`) — conta em atraso: dias, multa 2%, juros 1% a.m. pro rata, correção

## 🔜 Rodada 14 — próxima (planejada)
- 📄 Scanner de Documentos — foto de documento → recorte/endireitar → PDF
- 📊 Gerador de Gráficos — cola dados → gráfico bonito → PNG/SVG
- 📶 Compartilhar na Rede — compartilhar pasta na rede com senha + QR
- 📔 Diário Criptografado — diário pessoal com busca e humor do dia
- 🎨 Quadro Branco Colaborativo — desenho compartilhado na rede local
