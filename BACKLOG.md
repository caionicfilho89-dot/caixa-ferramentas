# 🧰 Backlog da Caixa de Ferramentas

Meta: a maior caixa de ferramentas offline do mundo. Os agentes constroem em rodadas de 5;
o Claude revisa, corrige, commita, integra na Caixa e gera instalador.

Regras de toda ferramenta: offline sempre que possível, UI pt-BR, tema escuro padrão,
módulos auxiliares com prefixo único, testada (py_compile + lógica + GUI offscreen),
nada que sirva pra golpe/ataque a terceiros.

## ✅ Na Caixa
1–17 (kit-pdf … gps-falso) · 18 Ferramentas BR (74 funções) · 19–23 Rodada 1 (v1.4.0) · 24–28 Rodada 2 · 29–33 Rodada 3 · 34–38 Rodada 4 · 39–43 Rodada 5 · 44–48 Rodada 6 · 49–53 Rodada 7 · 54–58 Rodada 8 · 59–63 Rodada 9 (no código, sem build)

## ✅ Rodada 1 (integrada na v1.4.0)
- 🛡️ Kit do Hacker — codificar/decodificar, hash, JWT, timestamp
- 💻 Ferramentas Dev — JSON/XML/SQL, regex, diff, cron
- 💰 Calculadora CLT — líquido, férias, 13º, rescisão (tabelas 2026)
- 📏 Conversor de Unidades e Moedas
- 💸 Pix & Boleto — gerar Pix pra receber, ler Pix, conferir boleto

## 📋 Próximas rodadas (ordem de prioridade)
### ✅ Rodada 2 — dia a dia (integrada)
- 💵 Finanças pessoais — juros compostos, financiamento SAC/Price, CDB x poupança x Tesouro, dividir conta
- ⏱️ Tempo — pomodoro, cronômetro, timer, alarme, desligar o PC agendado
- 📝 Notas Markdown — editor com prévia, pastas, busca
- ✅ Tarefas e lembretes — to-do com prazo + aviso na bandeja
- 📅 Calendário BR — feriados nacionais, dias úteis entre datas, contagem regressiva

### ✅ Rodada 3 — PC (integrada)
- 📊 Monitor do sistema — CPU/RAM/disco/rede ao vivo, processos, temperatura se der
- 🖥️ Info do PC — hardware, Windows, bateria (saúde), drivers
- 🚀 Inicialização — ver/desativar programas que abrem com o Windows
- 🗜️ Compactador — ZIP criar/extrair (com senha), ver conteúdo
- 🔐 Criptografar arquivos — trancar/destrancar arquivo com senha (AES)

### ✅ Rodada 4 — mídia (integrada)
- 🖼️ Editor de imagem rápido — cortar, redimensionar, girar, marca d'água, filtros
- 🎙️ Gravador de voz — microfone → MP3/WAV
- 🎨 Paletas de cores — gerar paleta harmônica, extrair cores de uma foto
- 📷 Webcam — espelho, foto, gravação curta
- 🔤 Visualizador de fontes — ver todas as fontes instaladas com texto de exemplo

### ✅ Rodada 5 — rede e diversão (integrada)
- 🌐 Rede — meu IP, ping, DNS, traceroute, Wi-Fi conectado, teste de velocidade
- 🎲 Sorteios — amigo secreto, dividir times, roleta, cara ou coroa, dados
- 🏋️ Saúde — IMC, água por dia, calorias, sono
- 📚 Flashcards — estudo com repetição espaçada (SM-2) [substituiu o expansor de texto]
- 🧮 Calculadora científica + gráfico de funções

### ✅ Rodada 6 — escritório (integrada)
- 📈 Visualizador de Planilhas — abre CSV/XLSX, filtra, ordena, soma, gráfico, exporta
- 🧾 Orçamentos e Recibos — pra MEI/autônomo: cadastro de clientes/itens, gera PDF com numeração
- 📇 Contatos — agenda offline, importa/exporta vCard e CSV, busca, aniversários
- 📖 Leitor de E-books — EPUB/TXT, marcadores, tamanho de fonte, modo noturno
- 🗂️ Organizador de Downloads — regras por tipo/data, MOVE (nunca apaga), desfazer

### ✅ Rodada 7 — dev e segurança defensiva (integrada)
- 🧪 Cliente de API — requisições HTTP estilo Postman (coleções, histórico, JSON bonito)
- 🗄️ Visualizador SQLite — abre .db, navega tabelas, roda SELECT, exporta CSV
- 🛡️ Checar cabeçalhos de segurança do SEU site — HSTS/CSP/X-Frame etc. com explicação
- 🔏 Certificado SSL — ver validade/emissor/cadeia de um domínio, avisar vencimento
- 🐍 Caderno Python — rodar snippets locais com saída, salvar trechos

### ✅ Rodada 8 — aprender e se divertir (integrada)
- ⌨️ Treino de digitação — PPM, precisão, textos em pt-BR
- 🧩 Sudoku — gerador com níveis, dicas, notas
- 🎹 Metrônomo e afinador — BPM com batida; afinador pelo microfone
- 🌍 Relógio mundial — fusos, conversor de horário, "melhor horário pra reunião"
- 🗺️ Quiz de geografia — bandeiras (desenhadas), capitais, estados do Brasil

### ✅ Rodada 9 — Windows turbinado (integrada)
- 🪟 Janelas — deixar qualquer janela sempre no topo, transparência, centralizar, layouts lado a lado
- 🔊 Volume por App — controlar o volume de cada programa separado, perfis
- 📁 Comparar Pastas — diferenças entre duas pastas (novos/alterados/faltando), copiar com prévia
- 🌱 Variáveis de Ambiente — ver/editar PATH e variáveis do usuário com backup
- 🖼️ Galeria de Fotos — visualizador rápido de pasta, slideshow, EXIF, girar sem perda

### 🔨 Rodada 10 — criadores e escrita (em construção)
- 📄 Currículo em PDF — modelos bonitos, preenche e exporta
- 🏷️ Etiquetas em lote — etiquetas/QR/códigos de barras pra imprimir em folha A4
- ✍️ Analisador de Texto — legibilidade, palavras repetidas, tempo de leitura, frases longas
- 🗣️ Texto para Fala — lê texto em voz alta com as vozes do Windows, salva WAV
- 🎵 Player de Música — toca a pasta de músicas, playlists, equalizador simples

