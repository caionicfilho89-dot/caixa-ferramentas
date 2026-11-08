"""Caixa de Ferramentas do Caio — um app só que reúne todas as ferramentas.

Grade de cartões; clicar abre a ferramenta (cada uma roda no seu processo, então nada
interfere em nada). Busca no topo, favoritos, abrir no boot, e dá pra adicionar
ferramentas novas pela própria Caixa (sem mexer no código). Tudo offline.

Config do usuário (favoritos + ferramentas adicionadas) em %LOCALAPPDATA%\\CaixaFerramentas.
"""
import json
import os
import subprocess
import sys
import urllib.request
import webbrowser

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (QApplication, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
                             QInputDialog, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton,
                             QScrollArea, QVBoxLayout, QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)   # C:\Users\caion — onde ficam as pastas das ferramentas
FROZEN = getattr(sys, "frozen", False)  # True quando empacotado num .exe (instalador)
APP_VERSION = "1.4.0"
REPO = "caionicfilho89-dot/caixa-ferramentas"
ACCENT = "#7c5cff"

CFG_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "CaixaFerramentas")
CFG = os.path.join(CFG_DIR, "config.json")
STARTUP = os.path.join(os.environ.get("APPDATA", ""),
                       r"Microsoft\Windows\Start Menu\Programs\Startup")
BOOT_LNK = os.path.join(STARTUP, "Caixa de Ferramentas.lnk")

# ferramentas de fábrica: (emoji, nome, descrição, pasta, script)
BUILTIN = [
    ("📄", "Kit de PDF", "Juntar, separar, girar, comprimir, imagens↔PDF", "kit-pdf", "kit_pdf.pyw"),
    ("🧹", "Faxina de Disco", "Vê o que ocupa o HD e manda pra Lixeira", "faxina-disco", "faxina.pyw"),
    ("♻️", "Recupera Arquivos", "Recupera arquivos apagados (carving / NTFS)", "recupera-arquivos", "recupera.pyw"),
    ("🧽", "Limpar Metadados", "Remove GPS/autor de fotos, PDF e Office", "limpa-metadados", "limpar_metadados.pyw"),
    ("🔳", "QR Code", "Gera e lê QR (link, wifi, contato…)", "qrcode-tool", "qrcode_tool.pyw"),
    ("✏️", "Print Anotador", "Captura a tela e anota (seta, tarja, texto)", "print-anotador", "print_anotador.pyw"),
    ("🖼️", "Conversor de Imagens", "Converte fotos em lote (inclusive HEIC)", "conversor-imagens", "conversor_imagens.pyw"),
    ("🔐", "Cofre de Senhas", "Gera senhas fortes + cofre criptografado", "cofre-senhas", "cofre_senhas.pyw"),
    ("🎥", "Gravador de Tela", "Grava a tela em MP4 ou GIF com som", "gravador-tela", "gravador_tela.pyw"),
    ("🎵", "Conversor Áudio/Vídeo", "Troca formato, extrai áudio, corta trecho", "conversor-av", "conversor_av.pyw"),
    ("🎨", "Capturador de Cores", "Conta-gotas da tela (HEX/RGB) + paleta", "capturador-cores", "capturador_cores.pyw"),
    ("📝", "Extrator de Texto", "OCR: copia o texto de uma área da tela", "extrator-texto", "extrator_texto.pyw"),
    ("🔍", "Busca de Arquivos", "Acha arquivo pelo nome na hora (Everything)", "busca-arquivos", "busca_arquivos.pyw"),
    ("✎", "Renomeador em Lote", "Renomeia vários arquivos com prévia", "renomeador", "renomeador.pyw"),
    ("📋", "Área de Transferência", "Histórico do que você copiou (Ctrl+Shift+V)", "area-transferencia", "area_transferencia.pyw"),
    ("⏱️", "Rastreador de Tempo", "Quanto tempo você passa em cada app", "rastreador-tempo", "rastreador_tempo.pyw"),
    ("🛰️", "GPS Falso", "Simula um GPS (NMEA) por TCP/UDP pra apps de navegação", "gps-falso", "gps_falso.pyw"),
    ("🇧🇷", "Ferramentas BR", "74 ferramentas: gerar/validar CPF, CNPJ, texto, matemática…", "ferramentas-br", "ferramentas_br.pyw"),
    ("🛡️", "Kit do Hacker", "Codificar/decodificar, hash, JWT, timestamp, caracteres ocultos", "kit-hacker", "kit_hacker.pyw"),
    ("💻", "Ferramentas Dev", "JSON/XML/SQL, regex ao vivo, comparar textos, cron, UUID", "ferramentas-dev", "ferramentas_dev.pyw"),
    ("💰", "Calculadora CLT", "Salário líquido, férias, 13º, rescisão, horas extras (2026)", "calculadora-clt", "calculadora_clt.pyw"),
    ("📏", "Conversor de Unidades", "14 tipos de medida + moedas com cotação", "conversor-unidades", "conversor_unidades.pyw"),
    ("💸", "Pix & Boleto", "Gera Pix pra receber, lê Pix e confere boleto", "pix-boleto", "pix_boleto.pyw"),
    ("💵", "Finanças", "Juros, financiamento SAC/Price, CDB x poupança, dividir conta", "financas", "financas.pyw"),
    ("⏲️", "Tempo", "Pomodoro, cronômetro, timers, alarmes, desligar o PC agendado", "tempo", "tempo.pyw"),
    ("🗒️", "Notas", "Notas em Markdown com prévia, busca e exportar PDF", "notas-md", "notas.pyw"),
    ("✅", "Tarefas", "Tarefas e lembretes; entende \"pagar luz amanhã 18h\"", "tarefas", "tarefas.pyw"),
    ("📅", "Calendário BR", "Feriados, dias úteis, contagem regressiva", "calendario-br", "calendario_br.pyw"),
    ("📊", "Monitor do Sistema", "CPU, memória, disco e rede ao vivo + processos", "monitor-sistema", "monitor_sistema.pyw"),
    ("🖥️", "Info do PC", "Hardware, Windows, discos, vídeo, bateria — relatório", "info-pc", "info_pc.pyw"),
    ("🚀", "Inicialização", "Liga/desliga o que abre com o Windows (com backup)", "inicializacao", "inicializacao.pyw"),
    ("🗜️", "Compactador", "ZIP, ZIP com senha AES e TAR.GZ: criar, abrir, extrair", "compactador", "compactador.pyw"),
    ("🔒", "Trancar Arquivos", "Tranca arquivos com senha (AES-256)", "cripto-arquivos", "cripto_arquivos.pyw"),
    ("🖌️", "Editor de Imagem", "Cortar, redimensionar, filtros, marca d'água, borrar área", "editor-imagem", "editor_imagem.pyw"),
    ("🎙️", "Gravador de Voz", "Grava o microfone em WAV/MP3 com medidor de volume", "gravador-voz", "gravador_voz.pyw"),
    ("🌈", "Paletas de Cores", "Harmonias, cores de uma foto, contraste WCAG, gradiente", "paletas", "paletas_cores.pyw"),
    ("📷", "Webcam", "Espelho, foto e vídeo curto com filtros", "webcam", "webcam_foto.pyw"),
    ("🔤", "Visualizador de Fontes", "Todas as fontes do PC, comparar e ver .ttf sem instalar", "fontes", "visualizador_fontes.pyw"),
    ("🌐", "Rede", "Minha conexão, IP público, ping, DNS e teste de velocidade", "rede", "ferramentas_rede.pyw"),
    ("🎲", "Sorteios", "Amigo secreto, dividir times, roleta, moeda e dados", "sorteios", "sorteios.pyw"),
    ("🏋️", "Saúde", "IMC, água, calorias, sono, FC e diário de peso", "saude", "saude.pyw"),
    ("🧮", "Calculadora Científica", "Calculadora, gráficos de funções e equações", "calculadora-cientifica", "calculadora_cientifica.pyw"),
    ("📚", "Flashcards", "Cartões de estudo com repetição espaçada", "flashcards", "flashcards.pyw"),
    ("📈", "Visualizador de Planilhas", "Abre CSV/Excel, filtra, soma, gráficos e exporta", "visualizador-planilhas", "visualizador_planilhas.pyw"),
    ("🧾", "Orçamentos e Recibos", "Orçamentos e recibos em PDF pra MEI/autônomo", "orcamentos", "orcamentos.pyw"),
    ("📇", "Contatos", "Agenda offline com vCard, WhatsApp e aniversários", "contatos", "contatos.pyw"),
    ("📖", "Leitor de E-books", "Lê EPUB/TXT com sumário, marcadores e modo noturno", "leitor-ebooks", "leitor_ebooks.pyw"),
    ("🗂️", "Organizador de Downloads", "Organiza a pasta por tipo (só move, com desfazer)", "organizador-downloads", "organizador.pyw"),
    ("🧪", "Cliente de API", "Requisições HTTP estilo Postman, coleções e cURL", "cliente-api", "cliente_api.pyw"),
    ("🗄️", "Visualizador SQLite", "Abre bancos .db, navega tabelas e roda SQL", "visualizador-sqlite", "visualizador_sqlite.pyw"),
    ("🛡️", "Boas Práticas do Site", "Nota A–F dos cabeçalhos de segurança do seu site", "cabecalhos-seguranca", "cabecalhos_seguranca.pyw"),
    ("🔏", "Certificado SSL", "Validade e detalhes do certificado + monitor de vencimento", "certificado-ssl", "certificado_ssl.pyw"),
    ("🐍", "Caderno Python", "Células de código estilo Jupyter, exporta .ipynb", "caderno-python", "caderno_python.pyw"),
    ("⌨️", "Treino de Digitação", "Textos em pt-BR, lições ABNT2, PPM e precisão", "treino-digitacao", "treino_digitacao.pyw"),
    ("🧩", "Sudoku", "Sudoku com 4 níveis, notas, dicas e estatísticas", "sudoku", "sudoku.pyw"),
    ("🎹", "Metrônomo e Afinador", "Metrônomo preciso + afinador pelo microfone", "metronomo", "metronomo.pyw"),
    ("✍️", "Analisador de Texto", "Legibilidade, frases longas, repetições e ortografia", "analisador-texto", "analisador_texto.pyw"),
    ("🌍", "Relógio Mundial", "Fusos, conversor de horário e planejar reunião", "relogio-mundial", "relogio_mundial.pyw"),
    ("🗺️", "Quiz de Geografia", "Capitais, bandeiras, continentes e estados do Brasil", "quiz-geografia", "quiz_geografia.pyw"),
    ("🪟", "Janelas", "Sempre no topo, transparência, metades/quadrantes e layouts", "janelas", "janelas.pyw"),
    ("🔊", "Volume por App", "Volume separado pra cada programa + perfis", "volume-apps", "volume_apps.pyw"),
    ("📁", "Comparar Pastas", "Diferenças entre duas pastas e cópia com prévia", "comparar-pastas", "comparar_pastas.pyw"),
    ("🌱", "Variáveis de Ambiente", "Editor do PATH e variáveis do usuário com backup", "variaveis-ambiente", "variaveis_ambiente.pyw"),
    ("🖼️", "Galeria de Fotos", "Miniaturas, slideshow, EXIF e girar JPG sem perda", "galeria-fotos", "galeria_fotos.pyw"),
    ("📄", "Currículo em PDF", "Monte seu currículo com 4 modelos e exporte PDF", "curriculo-pdf", "curriculo_pdf.pyw"),
    ("🏷️", "Etiquetas", "Etiquetas A4 com QR/código de barras e mala direta", "etiquetas", "etiquetas.pyw"),
    ("🗣️", "Texto para Fala", "Lê textos com as vozes do Windows e salva WAV/MP3", "texto-fala", "texto_fala.pyw"),
    ("🎵", "Player de Música", "Toca suas músicas: biblioteca, capas e playlists", "player-musica", "player_musica.pyw"),
    ("🔐", "Autenticador 2FA", "Códigos TOTP criptografados offline e leitor de QR", "autenticador-2fa", "fa_gui.pyw"),
    ("💳", "Controle de Gastos", "Lançamentos, categorias, orçamento e gráficos", "controle-gastos", "cg_gui.pyw"),
    ("🍳", "Receitas", "Caderno de receitas, ajuste de porções e lista de compras", "receitas", "rc_gui.pyw"),
    ("🚗", "Controle do Carro", "Abastecimentos, consumo (km/l) e manutenções", "controle-carro", "car_gui.pyw"),
    ("🎯", "Hábitos", "Checklist diário, sequências e calendário de progresso", "habitos", "hb_gui.pyw"),
    ("🚫", "Bloqueador de Sites", "Bloqueia sites editando o arquivo hosts do Windows", "site-blocker", "sb_gui.pyw"),
    ("🔍", "Detector de Duplicatas", "Escaneia pastas e deleta arquivos duplicados (MD5)", "duplicate-detector", "dd_gui.pyw"),
    ("🎲", "Gerador de Dados", "Gera dados falsos (nomes/emails) em CSV/JSON", "dummy-data-generator", "gd_gui.pyw"),
    ("📊", "Analisador de Espaço", "Analisa e lista o tamanho de arquivos e pastas", "disk-analyzer", "as_gui.pyw"),
    ("\U0001F4C8", "Monitor de Preços", "Monitora preços em sites, histórico, alertas de meta e gráfico", "price-monitor", "pm_gui.pyw"),
    ("🔑", "Gerador de Senhas", "Senhas seguras offline com medidor de força", "gerador-senhas", "gs_gui.pyw"),
    ("💱", "Conversor de Moedas", "Conversão offline entre BRL, USD, EUR, BTC e ETH", "conversor-moedas", "cm_gui.pyw"),
    ("\U0001F510", "Notas Criptografadas", "Cofre de notas com AES-256-GCM", "notas-criptografadas", "nc_gui.pyw"),
    ("🧾", "Gorjeta e Divisão", "Gorjeta, total da conta e divisão entre pessoas", "calculadora-gorjeta", "tg_gui.pyw"),
    ("\U0001F58C\ufe0f", "Quadro Branco", "Desenho livre, formas, texto, exportar PNG/PDF", "quadro-branco", "qb_gui.pyw"),
    ("\U0001F52A", "Canivete Suíço", "800 calculadoras inéditas: obra, elétrica, solar, saúde, engenharia…", "canivete", "canivete.pyw"),
    ("\U0001F4C4", "Scanner de Documentos", "Endireita perspectiva em 4 cantos, P&B sem sombra e gera PDF", "scanner-documentos", "scn_gui.pyw"),
    ("\U0001F4E1", "Compartilhar na Rede", "Envia e recebe arquivos PC ↔ celular via Wi-Fi com QR Code", "compartilhar-rede", "lan_gui.pyw"),
    ("\U0001F4AC", "Editor de Legendas", "SRT/VTT/ASS: sincronia, FPS, auditoria de leitura (CPS) e limpeza", "editor-legendas", "lg_gui.pyw"),
    ("\U0001F9EA", "Teste de Periféricos", "Teclado ABNT2 (rollover), mouse (duplo clique/Hz), dead pixel e som", "teste-hardware", "th_gui.pyw"),
    ("\U0001F9E0", "Mapa Mental", "Diagramas em árvore com curvas Bézier, atalhos e exportar PNG/PDF", "mapa-mental", "mm_gui.pyw"),
    ("\U0001F4CB", "Quadro Kanban", "Gestão ágil em colunas, limites WIP, Story Points e CSV", "quadro-kanban", "kb_gui.pyw"),
    ("\U0001F6E1\ufe0f", "Auditoria de Portas", "Portas TCP/UDP abertas, processos donos (PID) e exposição na rede", "auditoria-pc", "aud_gui.pyw"),
    ("\U0001F52C", "Inspetor de Executáveis", "Análise PE (.exe/.dll), seções, entropia UPX, hashes e strings", "inspetor-executavel", "dk_gui.pyw"),
    ("\U0001F39E\ufe0f", "Estúdio de GIF & Sprites", "Cria e extrai GIFs animados, efeito Boomerang e Spritesheets", "estudios-gif", "gif_gui.pyw"),
    ("\U0001F9E9", "Cofre de Snippets", "Comandos CLI, SQL e Docker com variáveis {{nome:padrao}} ao vivo", "cofre-snippets", "snip_gui.pyw"),
    ("\U0001F4F0", "Leitor de Feeds RSS", "Agregador online de notícias e blogs RSS/Atom com leitura limpa", "leitor-rss", "rss_gui.pyw"),
    ("\U0001F527", "Gerenciador de Serviços", "Inspeciona, filtra serviços de terceiros e controla via sc.exe/UAC", "gerenciador-servicos", "svc_gui.pyw"),
    ("\U0001F4F6", "Analisador de Wi-Fi", "Espectro de canais 2.4/5 GHz, melhor canal e senhas Wi-Fi salvas", "analisador-wifi", "wfi_gui.pyw"),
    ("\U0001F50E", "Auditor de SEO & Links", "Audita páginas web, OpenGraph, títulos H1–H6 e links quebrados", "auditor-seo", "seo_gui.pyw"),
    ("\U0001F4D0", "Corte de Chapas 2D", "Plano de corte guilhotina pra MDF, vidro e metal com mapa visual", "corte-chapas", "ccp_gui.pyw"),
    ("\U0001F9EC", "Comparador de Configs", "Diff semântico e conversor entre JSON, CSV, INI e .env", "comparador-dados", "dfx_gui.pyw"),
    ("\U0001F39B\ufe0f", "Laboratório de Áudio", "Sintetizador ADSR, acordes, ondas binaurais de foco e espectro FFT", "laboratorio-audio", "syn_gui.pyw"),
    ("\u26A1", "Automação & Macros", "Grava e executa macros de mouse e teclado (Win32) com captura F8", "gravador-macros", "mcr_gui.pyw"),
    ("\U0001F310", "Receptor de Webhooks", "Servidor Mock HTTP local, inspetor de headers/payload e gerador cURL", "inspetor-http", "prx_gui.pyw"),
    ("\U0001F52D", "Planetário & Efemérides", "Abóbada celeste 360°, fases da Lua, nascer do Sol e planetas ao vivo", "planetario", "ast_gui.pyw"),
    ("\U0001F4E6", "Código de Barras 1D", "Gera e valida EAN-13, EAN-8, Code-128B e ITF-14 + lote sequencial", "codigo-barras", "bar_gui.pyw"),
    ("\U0001F9EA", "Laboratório de Química", "Massa molar com hidratos, balanceador estequiométrico e elementos", "laboratorio-quimica", "chm_gui.pyw"),
    ("\U0001F3E6", "Amortização & Consórcio", "Simulador de amortização extra SAC/PRICE e Consórcio vs Financiamento", "comparador-credito", "crd_gui.pyw"),
    ("\U0001F4E1", "Scanner de Rede Local", "Descobre dispositivos na LAN (ARP), fabricante MAC OUI e portas TCP", "scanner-rede", "lsc_gui.pyw"),
    ("\u26A1", "Simulador de Circuitos", "Malhas de resistores, divisor de tensão, filtro RC (Bode) e NE555", "simulador-circuitos", "elt_gui.pyw"),
    ("\U0001F9EC", "Bioinformática & DNA", "Transcrição DNA→mRNA→Proteína, enzimas de restrição e alinhamento", "laboratorio-dna", "dna_gui.pyw"),
    ("\U0001F4C8", "Analisador de Logs SIEM", "Audita logs Apache/Nginx/JSONL, detecta SQLi/XSS e Eventos do Windows", "analisador-logs", "lga_gui.pyw"),
    ("\U0001F5FA\ufe0f", "Estúdio de Rotas GPX", "Trilhas GPX, distância geodésica Haversine e perfil altimétrico D+", "estudio-rotas", "gpx_gui.pyw"),
    ("\U0001F4D0", "Calculadora de Matrizes", "Determinante, inversa, autovalores, produto A×B e sistemas Ax=b", "calculadora-matrizes", "mtx_gui.pyw"),
    ("\U0001F6E1\ufe0f", "Gerenciador de Firewall", "Bloqueia internet de programas .exe e cria regras de portas TCP/UDP", "gerenciador-firewall", "fwl_gui.pyw"),
    ("\U0001F433", "Estúdio Docker", "Gerador de stacks docker-compose.yml, auditor CIS Dockerfile e containers", "painel-docker", "dck_gui.pyw"),
    ("\U0001F4CA", "Laboratório de Estatística", "Quartis, IC 95%, outliers Tukey IQR, histograma e regressão linear", "laboratorio-estatistica", "stt_gui.pyw"),
    ("\U0001FA7A", "Prontuário & Exames", "Avalia exames de sangue, controla fim de caixa de remédios e ficha SOS", "ficha-medica", "med_gui.pyw"),
    ("\U0001F3B9", "Estúdio Piano Roll & MIDI", "Sequenciador musical, escalas, síntese WAV e exportador binário .MID", "estudio-midi", "mid_gui.pyw"),
    ("\U0001F5D3\ufe0f", "Simulador Cron & Agendador", "Tradutor Cron com próximas 10 execuções e agendador Windows schtasks", "agendador-tarefas", "sch_gui.pyw"),
    ("\U0001F331", "Horta & Adubação NPK", "Dimensiona canteiros, adubo NPK, calagem pH e plantas companheiras", "horta-jardim", "agr_gui.pyw"),
    ("\U0001F50D", "Inspetor de Processos", "Árvore Pai/Filho (PPID→PID), linha de comando CLI e congelar/retomar", "inspetor-processos", "prc_gui.pyw"),
    ("\U0001F4D0", "Estúdio Vetorial SVG", "Gerador paramétrico de ícones/selos SVG, minificador XML e PNG", "estudio-svg", "svg_gui.pyw"),
    ("\U0001F4FB", "Rádio Amador & Morse", "Sintetizador CW Morse em WAV, fonética OTAN e antena dipolo/ROE", "radio-morse", "mrs_gui.pyw"),
    ("\U0001F4E6", "Cubagem & Cargas 3D", "Encaixe 3D em paletes/containers/baús e peso cubado aéreo/rodoviário", "cubagem-cargas", "cub_gui.pyw"),
    ("\U0001F510", "Chaves SSH & Config", "Gera chaves Ed25519/RSA, fingerprint SHA256, RandomArt e ~/.ssh/config", "gerador-ssh", "ssk_gui.pyw"),
    ("\U0001F4C3", "Leitor de NF-e XML", "Audita impostos ICMS/IPI/PIS/COFINS, itens NCM/CFOP e valida chave 44 dígitos", "leitor-nfe", "nfe_gui.pyw"),
    ("\u265F\ufe0f", "Estúdio de Xadrez", "Tabuleiro interativo, lances legais, notação FEN e partidas históricas", "estudio-xadrez", "chz_gui.pyw"),
    ("\U0001F310", "Arquiteto de Sub-redes", "Cálculo CIDR IPv4/IPv6 e alocador de sub-redes VLSM sem colisão", "calculadora-subrede", "ipm_gui.pyw"),
    ("\U0001F680", "Simulador de Física", "Cinemática e balística 2D com gravidade e mecânica orbital", "simulador-fisica", "fsc_gui.pyw"),
    ("\U0001F4DD", "Estúdio Markdown & TeX", "Editor Markdown ao vivo com fórmulas TeX, tabelas GFM e exportador HTML", "estudio-markdown", "mdx_gui.pyw"),
    ("\U0001F3E6", "Gerador de Extratos OFX", "Emulador de transações bancárias e gerador de arquivos OFX 1.02 para ERPs", "gerador-ofx", "ofx_gui.pyw"),
    ("\U0001F512", "Gerador de Certificados SSL", "Cria certificados X.509 v3 autoassinados com extensões SAN e chaves RSA", "gerador-ssl", "gsl_gui.pyw"),
    ("\U0001F3B5", "Estúdio de Áudio & Ondas", "Sintetizador de formas de onda (seno, quadrada, dente, ruído) e WAV", "estudio-som", "som_gui.pyw"),
    ("\U0001F52C", "Laboratório de Óptica", "Simulador da Lei de Snell, refração da luz, reflexão total e lentes", "simulador-optica", "opt_gui.pyw"),
    ("\U0001F9ED", "Conversor de Coordenadas", "Conversão entre Graus Decimais (DD), GMS e Projeção Plana UTM WGS84", "conversor-coordenadas", "geo_gui.pyw"),
    ("\u26A1", "Benchmark de Memória & SSD", "Testa a taxa real de transferência da memória RAM (GB/s) e do disco com fsync", "benchmark-pc", "bmk_gui.pyw"),
    ("\U0001F3B2", "Análise Combinatória & Loto", "Combinações, arranjos, permutações e probabilidades de loterias", "calculadora-combinatoria", "cmb_gui.pyw"),
    ("\U0001F510", "Estúdio de Cifras Clássicas", "Criptografia histórica: César, Vigenère, Atbash, Rail Fence e frequências", "estudio-cifras", "cfr_gui.pyw"),
    ("\u2712\ufe0f", "Estúdio de Tipografia", "Escalas modulares harmônicas (H1-Small), pareamento de fontes e CSS", "estudio-tipografia", "tip_gui.pyw"),
    ("\U0001F988", "Inspetor de Pacotes PCAP", "Analisador de capturas de rede Wireshark/tcpdump Ethernet/IP/TCP/UDP", "inspetor-pcap", "pcp_gui.pyw"),
    ("\u23F1\ufe0f", "Cronômetro & Relógio Xadrez", "Cronometragem esportiva com voltas e relógio de xadrez com incremento", "estudio-cronometro", "crn_gui.pyw"),
    ("\U0001F333", "Árvore de Decisão & ID3", "Algoritmo ID3, cálculo de Entropia de Shannon e Ganho de Informação", "arvore-decisao", "tre_gui.pyw"),
    ("\U0001F50D", "Inspetor de Regex", "Testador de expressões regulares ao vivo com grupos e medição em milissegundos", "inspetor-regex", "rgx_gui.pyw"),
    ("\U0001F578\ufe0f", "Estúdio de Grafos & Dijkstra", "Modelagem de topologias de rede, algoritmo de Dijkstra e menor caminho", "estudio-grafos", "grf_gui.pyw"),
    ("\U0001F50C", "Simulador de Portas Lógicas", "Álgebra booleana, portas lógicas, tabelas-verdade e mapa de Karnaugh", "simulador-logica", "lgc_gui.pyw"),
    ("\U0001F3B5", "Analisador de Áudio & FFT", "Espectrograma FFT, detecção de notas e harmônicos, tom puro e medidor dBFS", "analisador-audio-fft", "fft_gui.pyw"),
    ("\U0001F6E1\ufe0f", "Validador de JSON Schema", "Validação Draft-07 de dados JSON, inferência automática e detecção de erros", "validador-json-schema", "jsc_gui.pyw"),
    ("\u2699\ufe0f", "Calculadora de Engrenagens", "Engrenagens cilíndricas de dentes retos, relação de redução, RPM e torque", "calculadora-engrenagens", "grs_gui.pyw"),
    ("\U0001F5FA\ufe0f", "Gerador de Sitemap & Robots", "Protocolo sitemaps.org XML, gerador de robots.txt e validação de indexação", "gerador-sitemap", "stm_gui.pyw"),
    ("🪐", "Simulador Gravitacional N-Corpos", "Mecânica celeste newtoniana, órbitas Keplerianas, 3 corpos e pontos de Lagrange", "simulador-gravitacional-n-corpos", "nbd_gui.pyw"),
    ("🏗️", "Calculadora de Concreto Armado", "Dimensionamento de vigas NBR 6118 / Eurocode, armadura longitudinal e estribos", "calculadora-concreto-armado", "cnc_gui.pyw"),
    ("🗜️", "Compressão de Huffman & Entropia", "Codificação de Huffman, árvore binária, entropia de Shannon e economia de espaço", "estudio-compressao-huffman", "huf_gui.pyw"),
    ("🧬", "Laboratório de Autômatos Celulares", "Conway Game of Life 2D, autômatos de Wolfram 1D (Regra 30/90/110) e Formiga de Langton", "simulador-automato-celular", "cll_gui.pyw"),
    ("🌍", "Analisador de Geo IP & Rede", "Geolocalização de IP, consulta ASN, distância de Haversine e latência de fibra", "analisador-geo-ip", "gip_gui.pyw"),
    ("🎲", "Estatística & Inferência Bayesiana", "Teorema de Bayes, paradoxo do falso positivo em testes e modelo Beta-Binomial", "calculadora-estatistica-bayesiana", "bys_gui.pyw"),
    ("🍖", "Calculadora de Churrasco", "Carne por pessoa, carvão, bebidas, custos e rateio", "calculadora-churrasco", "chu_gui.pyw"),
    ("⛽", "Combustível e Viagem", "Etanol x gasolina, custo de viagem, paradas, CO₂ e consumo médio", "calculadora-combustivel-viagem", "cbv_gui.pyw"),
    ("😴", "Calculadora do Sono", "Ciclos de 90 min, débito de sono, jet lag social e cafeína", "calculadora-sono", "sno_gui.pyw"),
    ("🥗", "Calculadora de Nutrição", "IMC, TMB, gasto diário, macros, % de gordura e água", "calculadora-nutricao", "ntr_gui.pyw"),
    ("❄️", "Dimensionador de Ar-Condicionado", "BTUs do ambiente, consumo inverter x convencional e payback", "calculadora-ar-condicionado", "btu_gui.pyw"),
    ("🧾", "Simples Nacional e MEI", "DAS por anexo, alíquota efetiva, Fator R e limites do MEI", "calculadora-simples-nacional", "snl_gui.pyw"),
    ("🧠", "Flashcards com Repetição Espaçada", "Estudo com algoritmo SM-2, baralhos, importação CSV e estatísticas", "flashcards-repeticao", "fla_gui.pyw"),
    ("🌀", "Simulador de Pêndulo Duplo", "Caos em tempo real com RK4, rastro, energia e pêndulo gêmeo", "simulador-pendulo-duplo", "pdl_gui.pyw"),
    ("🎨", "Gerador de Paletas de Cores", "Harmonias, HEX/RGB/HSL/CMYK, contraste WCAG e exportação CSS", "gerador-paleta-cores", "pal_gui.pyw"),
    ("📆", "Calculadora de Datas", "Dias úteis com feriados, somar datas, idade exata e semana ISO", "calculadora-datas", "dts_gui.pyw"),
    ('🔢', 'Conversor de Bases & IEEE-754', 'Bases 2 a 36, complemento de 2, bits de float32/64 e operações bit a bit', 'conversor-bases', 'bse_gui.pyw'),
    ('🏖️', 'Simulador de Aposentadoria', 'Independência financeira com taxa real (Fisher), meta pela regra dos 4% e gráfico', 'simulador-aposentadoria', 'apo_gui.pyw'),
    ('🆔', 'Gerador de Identificadores', 'UUID v4/v5/v7, ULID, NanoID, decodificador de Snowflake e risco de colisão', 'gerador-identificadores', 'uid_gui.pyw'),
    ('🎨', 'Contraste WCAG & Daltonismo', 'Razão de contraste AA/AAA, cor sugerida e simulação de protanopia/deuteranopia', 'contraste-wcag', 'wcg_gui.pyw'),
    ('🌈', 'Código de Cores de Resistores', 'Faixas 4/5/6, valor para cores, SMD/EIA-96, séries E e melhor par série/paralelo', 'codigo-resistores', 'res_gui.pyw'),
    ('✍️', 'Números por Extenso & Romanos', 'Valores para cheque e recibo, cardinais, ordinais, feminino e algarismos romanos', 'numero-extenso', 'ext_gui.pyw'),
    ('⏰', 'Explicador de Cron', 'Traduz expressões cron para português e lista as próximas 20 execuções', 'explicador-cron', 'crx_gui.pyw'),
    ('🧱', 'Calculadora de Obra', 'Tinta com combinação de latas, pisos, caixas, argamassa e rejunte', 'calculadora-obra', 'obr_gui.pyw'),
    ('🔑', 'Decodificador de JWT', 'Decodifica, verifica HS256/384/512, gera tokens e audita segredos fracos', 'decodificador-jwt', 'jwt_gui.pyw'),
    ('📶', 'Calculadora de Banda & Armazenamento', 'Tempo de download, bitrate de vídeo, HD para CFTV/NVR e capacidade RAID', 'calculadora-banda', 'bnd_gui.pyw'),
    ("📐", "Analisador de Benford", "Lei de Benford no 1º dígito, χ², MAD Nigrini e auditoria de anomalias em CSV", "analisador-benford", "bnf_gui.pyw"),
    ("🎛️", "Simulador de Controle PID", "Planta 1ª ordem + atraso, resposta ao degrau, overshoot, Ziegler–Nichols e Cohen–Coon", "simulador-controle-pid", "pid_gui.pyw"),
    ("⏳", "Teoria das Filas", "M/M/1, M/M/c, Erlang-C, Lei de Little e dimensionamento de servidores por SLA", "teoria-filas", "qth_gui.pyw"),
    ("🧮", "Laboratório de CRC", "CRC-8/16/32, Adler-32, Fletcher-16, checksum Internet RFC 1071 e verificação", "laboratorio-crc", "crc_gui.pyw"),
    ("⚡", "Analisador de CPU & Topologia", "Telemetria por núcleo lógico, frequências MHz, modos de tempo e bateria", "analisador-cpu-termico", "cpt_gui.pyw"),
    ("📈", "Calculadora Black-Scholes & Gregas", "Precificação de opções européias, Letras Gregas, volatilidade implícita e payoff", "calculadora-financeira-black-scholes", "bsc_gui.pyw"),
    ("💧", "Calculadora Hidráulica de Tubulações", "Perda de carga Darcy-Weisbach, Hazen-Williams, Reynolds e motobombas", "calculadora-hidraulica-tubulacoes", "hdr_gui.pyw"),
    ("🔄", "Simulador de Circuitos RC & RLC", "Resposta ao degrau temporal, filtros passa-baixa/alta, ressonância e amortecimento", "simulador-circuitos-rc-rlc", "rlc_gui.pyw"),
    ("🗄️", "Formatador & Analisador de SQL", "Prettifier de consultas SQL, indentação de subqueries, AST e validação de sintaxe", "formatador-sql-ast", "sqf_gui.pyw"),
    ("📊", "Gerador de Diagramas de Sequência", "Diagramas UML de sequência, mensagens síncronas/retorno, notas e exportador SVG", "gerador-diagramas-sequence", "seq_gui.pyw"),
    ("🏃", "Ritmo & Corrida", "Ritmo↔velocidade, tempo de prova, splits, previsão Riegel, VO2max e zonas de FC", "pace", "pac_gui.pyw"),
    ("📡", "Calculadora RF & dBm", "dBm/mW/W, somar potências, freq↔λ, FSPL, orçamento de enlace e VSWR", "rf-calculo", "rfc_gui.pyw"),
    ("⚖️", "Juros de Mora & Multa", "Atualiza conta em atraso: dias, multa, juros de mora pro rata e correção", "juros-mora", "jmr_gui.pyw"),
    ("🔤", "Inspetor Unicode", "Codepoints, categorias, blocos, NFC/NFD/NFKC/NFKD e busca por nome Unicode", "inspetor-unicode", "uni_gui.pyw"),
    ("🎲", "Simulador Monte Carlo", "Estimativa de π, integração 1D por amostragem e agulha de Buffon", "simulador-monte-carlo", "mtc_gui.pyw"),
    ("🧭", "Calculadora de Quaternions", "Álgebra de Hamilton, eixo-ângulo, rotação 3D, matriz R e SLERP", "calculadora-quaternions", "qtn_gui.pyw"),
    ("🔊", "Codificador Fonético", "Soundex, Metaphone, Levenshtein e detecção de nomes duplicados", "codificador-fonetico", "phn_gui.pyw"),
    ("🎲", "Laboratório de Dados RPG", "Distribuição exata de NdM+K, chance de alvo, vantagem/desvantagem e histograma", "dados-rpg", "rpg_gui.pyw"),
    ("🧭", "Navegação & Rumo", "Distância e rumo entre pontos (ortodrômica/loxodrômica), ponto de chegada e ETA", "navegacao", "nav_gui.pyw"),
    ("🤰", "Calculadora Gestacional", "DPP (Naegele), semanas de gestação, trimestre e concepção pela DUM ou ultrassom", "gestacional", "gst_gui.pyw"),
    ("🌸", "Filtro de Bloom", "Dimensiona m/k, constrói filtro e consulta com taxa de falso positivo", "filtro-bloom", "blm_gui.pyw"),
    ("📈", "Estúdio de Splines", "Spline cúbico natural, Catmull–Rom e avaliação S(x) com gráfico", "estudio-splines", "spl_gui.pyw"),
    ("🌡️", "Índice de Conforto Térmico", "Heat Index NWS, Wind Chill, Humidex e ponto de orvalho", "calculadora-indice-conforto", "wci_gui.pyw"),
    ("🎒", "Otimizador da Mochila", "Mochila 0/1 por programação dinâmica e cota fracionária gulosa", "otimizador-mochila", "knp_gui.pyw"),
    ("⚙️", "Calculadora de Motores Elétricos", "Potência mecânica, escorregamento s, torque nominal, rendimento e fator de potência", "calculadora-motores-eletricos", "mot_gui.pyw"),
    ("🏛️", "Calculadora de Acústica de Salas", "Tempo de reverberação RT60 (Sabine/Eyring), frequência de Schroeder e modos próprios", "calculadora-acustica-salas", "acu_gui.pyw"),
    ("🔌", "Calculadora de Transformador de Potência", "Cálculo de núcleo Ae, espiras por volt, bitolas AWG e perdas do transformador", "calculadora-transformador-potencia", "trf_gui.pyw"),
    ("🔐", "Estúdio Criptografia Curvas Elípticas", "Aritmética de Weierstrass curta, multiplicação escalar e simulação ECDH", "estudio-criptografia-curvas-elipticas", "ecc_gui.pyw"),
    ("🧱", "Analisador de Difusão de Calor", "Condução 1D de Fourier em paredes compostas, valor U, valor R e perfil térmico", "analisador-difusao-calor", "thm_gui.pyw"),
    ("💳", "Validador de Cartão de Crédito", "Algoritmo de Luhn Módulo 10, identificação ISO/IEC 7812, bandeiras e gerador sandbox", "validador-formato-cartao-credito", "lhn_gui.pyw"),
    ("⬜", "Código de Gray", "Conversão bin↔Gray refletido, sequência n-bit e verificação de Hamming=1", "estudio-gray-code", "gry_gui.pyw"),
    ("🗜️", "Compressão RLE", "Run-Length Encoding de texto e bytes com tabela de corridas e razão", "compressao-rle", "rle_gui.pyw"),
    ("🔗", "Gerador Markov", "Cadeia de Markov de ordem k sobre corpus: treina e gera texto", "gerador-markov", "mkv_gui.pyw"),
    ("➗", "Fatoração de Primos", "Fatora inteiros (trial + Pollard Rho), Miller–Rabin e próximo primo", "fatoracao-primos", "prm_gui.pyw"),
    ("🧵", "Crochê & Tricô", "Pontos pela amostra, metragem de fio, agulhas mm/US/UK e distribuir aumentos", "croche", "trc_gui.pyw"),
    ("👗", "Conversor de Tamanhos", "Calçado BR/EU/US/UK/cm, roupa PP–XG e aro de anel (mm↔aro)", "tamanhos", "tam_gui.pyw"),
    ("🎂", "Calculadora de Festa", "Comida, bebida e descartáveis por convidados, duração e tipo de festa", "festa", "fst_gui.pyw"),
    ("✒️", "Estúdio Bézier", "Curvas de Bézier (Casteljau), ponto B(t), tangente e comprimento aproximado", "estudio-bezier", "bzr_gui.pyw"),
    ("🪣", "Token Bucket", "Simula rate limit com burst, recarga e fila de timestamps", "token-bucket", "tok_gui.pyw"),
    ("🕯️", "Temperatura de Cor", "Kelvin→RGB/HEX, mired, XYZ e mistura perceptualmente uniforme", "conversor-temperatura-cor", "ctk_gui.pyw"),
    ("📊", "Análise de Pareto", "Curva 80/20, classificação ABC e concentração de valor", "analisador-pareto", "prt_gui.pyw"),
    ("🎨", "Quadro Branco Colaborativo", "Desenho compartilhado na rede local (host/porta) em tempo real", "quadro-branco-colaborativo", "qc_gui.pyw"),
    ("📔", "Diário Criptografado", "Diário pessoal com senha (AES/Fernet), humor do dia e busca", "diario-criptografado", "dc_gui.pyw"),
    ("📈", "Gerador de Gráficos", "Cola dados e gera gráfico (barra/linha/pizza) e exporta SVG/PNG", "gerador-graficos", "gg_gui.pyw"),
    ("📉", "Alavancagem DOL/DFL/DCL", "Alavancagem operacional, financeira, combinada, equilíbrio e margem de segurança", "calculadora-alavancagem", "alg_gui.pyw"),
    ("📝", "Gerador Lorem Ipsum", "Gera palavras, frases, parágrafos ou N caracteres de placeholder", "gerador-lorem", "lor_gui.pyw"),
    ("📉", "Lei de Zipf", "Ranking de frequências, slope log-log e teste Zipf-like em textos", "analisador-zipf", "zpf_gui.pyw"),
    ("⏱️", "Conversor Epoch", "Unix epoch s/ms/µs/ns ↔ data UTC/local com detecção automática", "conversor-epoch", "epc_gui.pyw"),
    ("⭕", "Círculo de Mohr & Tensões 2D", "Tensões principais, cisalhamento máximo, rotação de planos e von Mises", "calculadora-tensao-cisalhamento-mohr", "mhr_gui.pyw"),
    ("📻", "Simulador Modulação AM & FM", "Modulação analógica, formas de onda temporais, índice μ/β e Regra de Carson", "simulador-modulacao-am-fm", "amf_gui.pyw"),
    ("🧠", "Estúdio de Redes Neurais MLP", "Perceptron multicamadas denso, backpropagation analítico e aprendizado SGD", "calculadora-redes-neurais-mlp", "mlp_gui.pyw"),
    ("✈️", "Perfis Aerodinâmicos NACA", "Aerofólios NACA 4 dígitos, camber, distribuição de espessura e coordenadas .DAT", "analisador-perfil-aerodinamico-naca", "nca_gui.pyw"),
    ("🧪", "Calculadora de Cinética Química", "Ordens de reação 0/1/2, tempos de meia-vida t½ e conversão por Arrhenius", "calculadora-cinetica-quimica", "knt_gui.pyw"),
    ("🔐", "Rede de Feistel & Cifras de Bloco", "Estrutura DES/Blowfish, S-Box/P-Box, reversibilidade e efeito avalanche", "estudio-criptografia-feistel-des", "fei_gui.pyw"),
    ("☕", "Calculadora de Café", "Proporção café/água por método (coado, V60, prensa, AeroPress, espresso) e extração", "calculadora-cafe", "cfe_gui.pyw"),
    ("🍺", "Calculadora de Cerveja", "ABV, OG/FG, IBU e SRM pra receita de cerveja artesanal", "calculadora-cerveja", "brw_gui.pyw"),
    ("📐", "Calculadora de Treliças 2D", "Treliças 2D pelo método da rigidez direta: forças nas barras e reações", "calculadora-trelicas-2d", "trs_gui.pyw"),
    ("🔗", "Links NTFS & Atalhos", "Cria links simbólicos, junctions e atalhos .lnk no Windows", "links-ntfs", "sym_gui.pyw"),
    ("🐠", "Calculadora de Aquário", "Volume real do aquário, dosagem e parâmetros da água", "calculadora-aquario", "aqu_gui.pyw"),
    ("🏛️", "Flambagem de Colunas (Euler)", "Carga crítica de Euler, índice de esbeltez e tensão admissível", "calculadora-flambagem-colunas-euler", "eul_gui.pyw"),
    ("🌱", "Calculadora de Hidroponia", "Solução nutritiva, EC/pH e dosagem de sais pra hidroponia", "calculadora-hidroponia", "hdp_gui.pyw"),
    ("🚲", "Marchas de Bicicleta", "Relação de marchas, desenvolvimento (m) e cadência x velocidade", "calculadora-marchas-bike", "bik_gui.pyw"),
    ("🔎", "Inspetor de Streams ADS", "Acha e inspeciona Alternate Data Streams (NTFS) escondidos em arquivos", "inspetor-ads", "ads_gui.pyw"),
    ("📦", "Planejador de Mudança", "Caixas, volume, checklist e inventário pra organizar uma mudança", "planejador-mudanca", "mdc_gui.pyw"),
]

QSS = """
QWidget { background:#0e1016; color:#e7e9f0; font:10pt 'Segoe UI'; }
#title { font:800 22pt 'Segoe UI'; }
#sub { color:#8a93a8; }
QLineEdit { background:#161a23; border:1px solid #2d3550; border-radius:12px; padding:10px 14px; font:12pt 'Segoe UI'; }
QLineEdit:focus { border:1px solid #7c5cff; }
QScrollArea { border:0; }
#card { background:#161a23; border:1px solid #232a3b; border-radius:16px; }
#card:hover { border:1px solid #7c5cff; background:#1a1f2b; }
#emoji { font:22pt 'Segoe UI Emoji'; }
#name { font:700 11pt 'Segoe UI'; }
#desc { color:#8a93a8; font:9pt 'Segoe UI'; }
#missing { color:#ff6b6b; font:9pt 'Segoe UI'; }
#star { color:#ffd166; font:12pt 'Segoe UI'; }
#section { color:#8a93a8; font:700 10pt 'Segoe UI'; }
QPushButton { background:#222a38; border:0; border-radius:9px; padding:8px 12px; }
QPushButton:hover { background:#2d3550; }
QPushButton:checked { background:#2a2740; color:#c9b8ff; }
#add { background:#1d2b22; }
#add:hover { background:#28402f; }
#update { background:#3a2f12; color:#ffd166; font-weight:600; }
#update:hover { background:#4a3c18; }
"""


def app_icon():
    pm = QPixmap(64, 64)
    pm.fill(QColor("transparent"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(ACCENT))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(6, 14, 52, 42, 10, 10)
    p.setBrush(QColor("#0e1016"))
    p.drawRoundedRect(24, 8, 16, 12, 4, 4)
    p.setBrush(QColor("#fff"))
    p.drawRect(30, 26, 4, 18)
    p.drawRect(25, 33, 14, 4)
    p.end()
    return QIcon(pm)


def pythonw():
    exe = sys.executable
    d = os.path.dirname(exe)
    cand = os.path.join(d, "pythonw.exe")
    return cand if os.path.exists(cand) else exe


def window_icon():
    ico = os.path.join(HERE, "caixa.ico")
    if os.path.exists(ico):
        return QIcon(ico)
    return app_icon()


def _ver_tuple(s):
    out = []
    for p in str(s).lstrip("vV").split("."):
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    return tuple(out)


class UpdateThread(QThread):
    """Checa (no GitHub) se saiu versão nova. Silencioso se falhar/sem internet."""
    found = pyqtSignal(str, str)  # tag, url

    def run(self):
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/releases/latest",
                headers={"User-Agent": "CaixaDeFerramentas"})
            data = json.load(urllib.request.urlopen(req, timeout=8))
            tag = data.get("tag_name", "")
            if tag and _ver_tuple(tag) > _ver_tuple(APP_VERSION):
                self.found.emit(tag, data.get("html_url", ""))
        except Exception:
            pass


def load_cfg():
    try:
        with open(CFG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"favorites": [], "extra_tools": []}


def save_cfg(cfg):
    os.makedirs(CFG_DIR, exist_ok=True)
    try:
        with open(CFG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


class Card(QFrame):
    def __init__(self, tool, caixa, fav):
        super().__init__(objectName="card")
        emoji, name, desc, folder, script = tool
        self.tool = tool
        self.key = folder
        self.caixa = caixa
        self.path = os.path.join(BASE, folder, script)
        self.exists = True if FROZEN else os.path.exists(self.path)
        self.setFixedSize(230, 120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 12, 10)
        lay.setSpacing(4)
        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(QLabel(emoji, objectName="emoji"))
        nm = QLabel(name, objectName="name")
        nm.setWordWrap(True)
        top.addWidget(nm, 1)
        if fav:
            top.addWidget(QLabel("★", objectName="star"), 0, Qt.AlignmentFlag.AlignTop)
        lay.addLayout(top)
        d = QLabel(desc, objectName="desc")
        d.setWordWrap(True)
        lay.addWidget(d, 1)
        if not self.exists:
            lay.addWidget(QLabel("não encontrada", objectName="missing"))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.caixa.open_tool(self)

    def _menu(self, pos):
        m = QMenu(self)
        is_fav = self.key in self.caixa.cfg["favorites"]
        a_fav = m.addAction("☆ Tirar dos favoritos" if is_fav else "⭐ Favoritar")
        a_folder = m.addAction("Abrir pasta")
        a_rm = None
        if any(self.key == t[3] for t in self.caixa.extra_tools):
            a_rm = m.addAction("Remover da Caixa")
        act = m.exec(self.mapToGlobal(pos))
        if act is a_fav:
            self.caixa.toggle_fav(self.key)
        elif act is a_folder:
            folder = os.path.dirname(self.path)
            if os.path.isdir(folder):
                os.startfile(folder)  # noqa: S606
        elif a_rm is not None and act is a_rm:
            self.caixa.remove_tool(self.key)


class Caixa(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Caixa de Ferramentas do Caio")
        self.setWindowIcon(window_icon())
        self.resize(800, 660)
        self.cfg = load_cfg()
        self.cfg.setdefault("favorites", [])
        self.cfg.setdefault("extra_tools", [])
        self.cfg.setdefault("uses", {})
        self.extra_tools = [tuple(t) for t in self.cfg["extra_tools"]]

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(10)

        head = QHBoxLayout()
        tt = QVBoxLayout()
        tt.setSpacing(2)
        tt.addWidget(QLabel("🧰 Caixa de Ferramentas", objectName="title"))
        self.sub = QLabel("", objectName="sub")
        tt.addWidget(self.sub)
        head.addLayout(tt)
        head.addStretch(1)
        self.update_btn = QPushButton("🔔  Atualizar")
        self.update_btn.setObjectName("update")
        self.update_btn.hide()
        self.update_btn.clicked.connect(self._open_update)
        self.boot_btn = QPushButton("🔌  Abrir no boot")
        self.boot_btn.setCheckable(True)
        self.boot_btn.setChecked(os.path.exists(BOOT_LNK))
        self.boot_btn.clicked.connect(self.toggle_boot)
        self.sc_btn = QPushButton("📌  Menu Iniciar")
        self.sc_btn.clicked.connect(self.make_shortcut)
        head.addWidget(self.update_btn, 0, Qt.AlignmentFlag.AlignTop)
        head.addWidget(self.boot_btn, 0, Qt.AlignmentFlag.AlignTop)
        head.addWidget(self.sc_btn, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(head)

        sr = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar ferramenta…")
        self.search.textChanged.connect(self.rebuild)
        sr.addWidget(self.search, 1)
        add = QPushButton("➕  Adicionar ferramenta", objectName="add")
        add.clicked.connect(self.add_tool)
        sr.addWidget(add)
        root.addLayout(sr)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.host = QWidget()
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(2, 4, 2, 4)
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.host)
        root.addWidget(self.scroll, 1)

        self.status = QLabel("", objectName="sub")
        root.addWidget(self.status)

        self.search.setFocus()
        self.rebuild()

        # checa atualização em segundo plano (silencioso se falhar)
        self._upd = UpdateThread()
        self._upd.found.connect(self._on_update)
        self._upd.start()

    def all_tools(self):
        return BUILTIN + self.extra_tools

    def _lay_section(self, title, tools, row):
        cols = 3
        if title:
            self.grid.addWidget(QLabel(title, objectName="section"), row, 0, 1, cols)
            row += 1
        col = 0
        for t in tools:
            self.grid.addWidget(Card(t, self, t[3] in self.cfg["favorites"]), row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1
        if col != 0:
            row += 1
        return row

    def rebuild(self):
        q = self.search.text().lower().strip()
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        tools = [t for t in self.all_tools()
                 if not q or q in t[1].lower() or q in t[2].lower()]
        if q:
            self._lay_section(None, tools, 0)
        else:
            favs = self.cfg["favorites"]
            uses = self.cfg["uses"]
            fav_tools = [t for t in tools if t[3] in favs]
            rest = [t for t in tools if t[3] not in favs]
            used = sorted([t for t in rest if uses.get(t[3], 0) > 0],
                          key=lambda t: -uses.get(t[3], 0))[:4]
            used_keys = {t[3] for t in used}
            todas = [t for t in rest if t[3] not in used_keys]
            row = 0
            if fav_tools:
                row = self._lay_section("★ Favoritos", fav_tools, row)
            if used:
                row = self._lay_section("🔥 Mais usadas", used, row)
            row = self._lay_section("Todas" if (fav_tools or used) else None, todas, row)
        self.sub.setText(f"{len(self.all_tools())} ferramentas prontas pra uso. Clique pra abrir.")

    # ---- abrir ----
    def open_tool(self, card):
        if not card.exists:
            QMessageBox.warning(self, "Ops", f"Não achei:\n{card.path}")
            return
        try:
            if FROZEN:
                # no instalador: o próprio exe abre a ferramenta (Caixa.exe --tool <chave>)
                subprocess.Popen([sys.executable, "--tool", card.key])
            else:
                subprocess.Popen([pythonw(), card.path], cwd=os.path.dirname(card.path))
            self.status.setText("Abrindo " + card.tool[1] + "…")
            self.cfg["uses"][card.key] = self.cfg["uses"].get(card.key, 0) + 1
            save_cfg(self.cfg)
            self.rebuild()
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Erro", str(e))

    # ---- atualização ----
    def _on_update(self, tag, url):
        self._update_url = url or f"https://github.com/{REPO}/releases/latest"
        self.update_btn.setText(f"🔔  Atualizar ({tag})")
        self.update_btn.show()
        self.status.setText(f"Saiu uma versão nova: {tag}. Clique em Atualizar.")

    def _open_update(self):
        webbrowser.open(getattr(self, "_update_url", f"https://github.com/{REPO}/releases/latest"))

    # ---- favoritos ----
    def toggle_fav(self, key):
        favs = self.cfg["favorites"]
        if key in favs:
            favs.remove(key)
        else:
            favs.append(key)
        save_cfg(self.cfg)
        self.rebuild()

    # ---- adicionar / remover ferramenta ----
    def add_tool(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Escolha o programa da ferramenta", BASE, "Python (*.pyw *.py)")
        if not path:
            return
        folder_full = os.path.dirname(path)
        folder = os.path.basename(folder_full)
        script = os.path.basename(path)
        if folder in [t[3] for t in self.all_tools()]:
            QMessageBox.information(self, "Já tem", "Essa ferramenta já está na Caixa.")
            return
        name, ok = QInputDialog.getText(self, "Nome", "Nome da ferramenta:",
                                        text=folder.replace("-", " ").title())
        if not ok or not name.strip():
            return
        emoji, _ = QInputDialog.getText(self, "Ícone", "Um emoji pro ícone (opcional):", text="🧩")
        desc, _ = QInputDialog.getText(self, "Descrição", "Descrição curta (opcional):", text="")
        tool = (emoji.strip() or "🧩", name.strip(), desc.strip(), folder, script)
        self.extra_tools.append(tool)
        self.cfg["extra_tools"] = [list(t) for t in self.extra_tools]
        save_cfg(self.cfg)
        self.rebuild()
        self.status.setText(f"“{name}” adicionada!")

    def remove_tool(self, key):
        self.extra_tools = [t for t in self.extra_tools if t[3] != key]
        self.cfg["extra_tools"] = [list(t) for t in self.extra_tools]
        if key in self.cfg["favorites"]:
            self.cfg["favorites"].remove(key)
        save_cfg(self.cfg)
        self.rebuild()

    # ---- boot / atalho ----
    def toggle_boot(self):
        if self.boot_btn.isChecked():
            ok = self._make_lnk(BOOT_LNK)
            if ok:
                self.status.setText("Vai abrir junto com o Windows.")
            else:
                self.boot_btn.setChecked(False)
        else:
            try:
                os.remove(BOOT_LNK)
            except OSError:
                pass
            self.status.setText("Não abre mais no boot.")

    def make_shortcut(self):
        start = os.path.join(os.environ.get("APPDATA", ""),
                             r"Microsoft\Windows\Start Menu\Programs")
        if self._make_lnk(os.path.join(start, "Caixa de Ferramentas.lnk")):
            QMessageBox.information(self, "Pronto",
                                    "Atalho criado! Procure por “Caixa de Ferramentas” no Menu Iniciar.")

    def _make_lnk(self, lnk):
        if FROZEN:
            target = sys.executable
            arg = ""
        else:
            target = pythonw()
            arg = os.path.abspath(__file__)
        ps = (
            "$w = New-Object -ComObject WScript.Shell; "
            f"$s = $w.CreateShortcut('{lnk}'); "
            f"$s.TargetPath = '{target}'; "
            f"$s.Arguments = '\"{arg}\"'; "
            f"$s.WorkingDirectory = '{HERE}'; "
            f"$s.IconLocation = '{target}'; "
            "$s.Save()"
        )
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           check=True, capture_output=True, creationflags=0x08000000)
            return True
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Não deu", f"Não consegui criar o atalho:\n{e}")
            return False


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    w = Caixa()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
