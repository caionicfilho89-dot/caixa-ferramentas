"""Caixa de Ferramentas do Caio — um app só que reúne todas as ferramentas.

Abre na tela Hoje (cartões vivos do PC) + barra que responde perguntas no topo.
A grade de cartões continua a um clique ("Todas as ferramentas"). Cada ferramenta
roda no seu processo. Favoritos, boot e adicionar ferramentas pela própria Caixa.

Config do usuário (favoritos + ferramentas adicionadas) em %LOCALAPPDATA%\\CaixaFerramentas.
"""
import json
import os
import subprocess
import time
import sys
import traceback
import urllib.request
import webbrowser

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame, QGridLayout,
                             QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox,
                             QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
                             QDialog, QTextBrowser, QSizePolicy)

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)   # C:\Users\caion — onde ficam as pastas das ferramentas
FROZEN = getattr(sys, "frozen", False)  # True quando empacotado num .exe (instalador)
# Modo teste (Cocaino): "--teste" na linha de comando ou CAIXA_TESTE=1. Não conta uso do Caio e marca tudo que
# abrir com "--teste", pra o carteiro fechar sozinho o que um teste esquecer aberto.
if "--teste" in sys.argv:
    os.environ["CAIXA_TESTE"] = "1"
MODO_TESTE = os.environ.get("CAIXA_TESTE") == "1"
APP_VERSION = "1.6.0"
REPO = "caionicfilho89-dot/caixa-ferramentas"
ACCENT = "#7c5cff"

# Peças do RUMO (tela Hoje + barra). Se faltar alguma, a Caixa cai na grade clássica.
try:
    import caixa_busca_ui as _caixa_busca_ui
    import caixa_home as _caixa_home
    import caixa_tema as _caixa_tema
    _RUMO_UI = True
except Exception:
    _caixa_busca_ui = None  # type: ignore
    _caixa_home = None  # type: ignore
    _caixa_tema = None  # type: ignore
    _RUMO_UI = False
    traceback.print_exc()

try:
    import caixa_arquivo as _caixa_arquivo
except Exception:
    _caixa_arquivo = None


def _carrega_ajuda():
    """Le AJUDA.json (sinopse/para_que/como_usar/exemplo por chave).

    Procura no bundle do .exe (sys._MEIPASS), ao lado deste arquivo (fonte/staged)
    e ao lado do executavel. Se nao achar, devolve {} e os cards usam a desc curta.
    """
    cands = []
    if getattr(sys, "_MEIPASS", None):
        cands.append(sys._MEIPASS)
    cands += [HERE, os.path.dirname(os.path.abspath(sys.executable))]
    for d in cands:
        p = os.path.join(d, "AJUDA.json")
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    dados = json.load(f)
                if isinstance(dados, dict):
                    return dados
            except Exception:
                pass
    return {}


AJUDA = _carrega_ajuda()


def _esc(t):
    import html
    return html.escape(str(t or ""))


def ajuda_html(nome, emoji, desc, chave):
    """HTML do dialogo 'Como usar'. Sem entrada no AJUDA.json, cai pra desc curta."""
    a = AJUDA.get(chave) or {}
    sin = a.get("sinopse") or desc
    h = [f"<h2 style='margin:0'>{_esc(emoji)} {_esc(nome)}</h2>",
         f"<h3 style='color:{ACCENT}'>O que é</h3><p>{_esc(sin)}</p>"]
    if a.get("para_que"):
        h.append(f"<h3 style='color:{ACCENT}'>Para que serve</h3><p>{_esc(a['para_que'])}</p>")
    passos = a.get("como_usar") or []
    if passos:
        h.append(f"<h3 style='color:{ACCENT}'>Passo a passo</h3><ol>"
                 + "".join(f"<li style='margin-bottom:4px'>{_esc(p)}</li>" for p in passos) + "</ol>")
    if a.get("exemplo"):
        h.append(f"<h3 style='color:{ACCENT}'>Exemplo</h3><p><i>{_esc(a['exemplo'])}</i></p>")
    if not a:
        h.append("<p style='color:#8a93a8'><i>Instruções detalhadas ainda não disponíveis para esta ferramenta.</i></p>")
    return "".join(h)


class AjudaDialog(QDialog):
    def __init__(self, nome, emoji, desc, chave, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Como usar — {nome}")
        self.resize(560, 520)
        lay = QVBoxLayout(self)
        tb = QTextBrowser()
        tb.setOpenExternalLinks(True)
        tb.setStyleSheet("QTextBrowser{background:#161a24;color:#e6e9f2;border:1px solid #2a3042;"
                         "border-radius:8px;padding:10px;font-size:14px;}")
        tb.setHtml(ajuda_html(nome, emoji, desc, chave))
        lay.addWidget(tb, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        ok = QPushButton("Fechar")
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        lay.addLayout(row)

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
    ("📻", "Circuito Ressonante LC/RLC", "Frequência de Thomson f0, fator de qualidade Q, banda passante e |Z(f)|", "analisador-circuito-ressonante-lc", "rls_gui.pyw"),
    ("🚀", "Dinâmica Orbital & Hohmann", "Transferência orbital de Hohmann, Delta-V, semi-eixo e tempo de voo", "calculadora-dinamica-orbital-hohmann", "hmn_gui.pyw"),
    ("💡", "Fotometria & Iluminação", "Método dos Lúmens (NBR 8995), Lux, Candelas e projeção de cone de luz", "calculadora-fotometria-lux-lumen", "lux_gui.pyw"),
    ("📦", "Enquadramento HDLC & CRC-16", "Protocolo ISO 13239, bit-stuffing de zeros, FCS CRC-16 e teste de canal", "gerador-analisador-codigo-hdlc-crc16", "hdl_gui.pyw"),
    ("🌡️", "Dilatação Térmica & Tensão", "Dilatação linear, superficial e volumétrica, folga de junta e tensão térmica", "calculadora-dilatacao-termica-tensao", "dlt_gui.pyw"),
    ("💎", "Difração de Raios-X (Bragg)", "Lei de Bragg, índices de Miller, extinção de simetria e difratograma XRD", "analisador-difracao-raios-x-bragg", "brg_gui.pyw"),
    ("🎱", "Bingo em Família", "Globo de 75/90 bolas com painel, desfazer, gerador de cartelas BINGO e conferência automática…", "bingo-familia", "bng_gui.pyw"),
    ("🧪", "Equações de Estado & Gases Reais", "Modelos Van der Waals, Redlich-Kwong e Peng-Robinson, fator Z, fugacidade e isotermas P-V", "calculadora-equacoes-estado-gases", "vdw_gui.pyw"),
    ("🍞", "Calculadora de Pão", "Porcentagem de padeiro com levain, receitas base, massa pelo peso, conversão de fermentos…", "calculadora-pao", "pao_gui.pyw"),
    ("🍕", "Calculadora de Pizza", "Massa por estilo e tamanho ou forma, fermento por tempo e temperatura, pizzas por pessoa e…", "calculadora-pizza", "pzz_gui.pyw"),
    ("🌸", "Ciclo Menstrual", "Registro dos ciclos com média, regularidade, previsão da próxima menstruação, ovulação e…", "ciclo-menstrual", "cic_gui.pyw"),
    ("🛒", "Comparador de Preços do Mercado", "Preço por kg, litro ou unidade com promoções leve-pague, 2ª unidade e desconto, melhor opção e…", "comparador-mercado", "mkt_gui.pyw"),
    ("💡", "Consumo de Energia da Casa", "kWh e custo por aparelho, conta com bandeira tarifária, maiores consumos, economia de trocas…", "consumo-energia", "kwh_gui.pyw"),
    ("🔤", "Conversor Base64 de Arquivos", "Arquivo↔Base64 (padrao/URL-safe), data URI e estimativa de expansao", "conversor-base64-arquivo", "b64_gui.pyw"),
    ("🪄", "Detector Magic / MIME", "Identifica tipo real pelo cabecalho, compara com a extensao e varre pastas por arquivos…", "detector-magic", "mag_gui.pyw"),
    ("🔬", "Diff Hex Binario", "Compara dois arquivos byte a byte com dump lado a lado, primeiro diff e similaridade", "diff-hex", "hxd_gui.pyw"),
    ("🍼", "Enxoval de Bebê", "Fraldas por tamanho e mês com custo e comparação com pano, roupas por clima e checklist do…", "enxoval-bebe", "enx_gui.pyw"),
    ("🖼️", "Extrator de Icones", "Extrai icones de EXE/DLL/ICO, conta recursos e salva PNG ou ICO associado", "extrator-icones", "ico_gui.pyw"),
    ("🛡️", "Inspetor ACL NTFS", "Le dono e permissoes NTFS, mostra icacls, concede leitura e reseta heranca", "inspetor-acl", "acl_gui.pyw"),
    ("🔏", "Inspetor PEM / Certificados", "Le PEM/DER locais: fingerprint SHA256, validade, SANs e extracao da cadeia de certificados", "inspetor-pem", "pem_gui.pyw"),
    ("🧳", "Mala de Viagem", "Checklist da mala por dias, clima, tipo de viagem e lavanderia, com peso estimado e limite da…", "mala-viagem", "mal_gui.pyw"),
    ("🍱", "Marmitas da Semana", "Cardápio de marmitas em rodízio, lista de compras em peso cru, custo por marmita e divisão…", "marmitas-semana", "mmt_gui.pyw"),
    ("👀", "Monitor de Pasta", "Observa criacao/alteracao/exclusao em tempo real, filtra por extensao e exporta log CSV/TXT", "monitor-pasta", "fwt_gui.pyw"),
    ("♠️", "Placar de Jogos de Cartas", "Placar por rodadas para buraco, canastra, uno, copas, pife e tranca, com meta, vencedor…", "placar-cartas", "plc_gui.pyw"),
    ("🃏", "Placar de Truco", "Placar de truco paulista com truco/seis/nove/doze, mão de onze e de ferro, quedas, desfazer e…", "placar-truco", "tru_gui.pyw"),
    ("💍", "Planejador de Casamento", "Orçamento por categoria, presença estimada por perfil de convidado, bebidas, salgados, mesas…", "planejador-casamento", "cas_gui.pyw"),
    ("🔒", "Quem Trava o Arquivo", "Lista processos com o arquivo aberto (Restart Manager) e testa acesso exclusivo", "quem-trava-arquivo", "lok_gui.pyw"),
    ("🪴", "Rega de Plantas", "Agenda de rega por espécie, estação, ambiente, vaso e material, com volume de água, dicas e…", "rega-plantas", "reg_gui.pyw"),
    ("🧩", "Simulador Precessao Giroscopica", "", "simulador-precessao-giroscopica", "gyr_gui.pyw"),
    ("🧹", "Tarefas da Casa e Mesada", "Divide tarefas domésticas por pontos e idade, rodízio semanal, checklist do feito e mesada por…", "tarefas-casa", "tcs_gui.pyw"),
    ("🧮", "Verificador de Hash", "MD5/SHA1/SHA256/SHA512, compara arquivos, confere SHA256SUMS e gera listas de checksum", "verificador-hash", "hsh_gui.pyw"),
    ("☀️", "Calculadora Fotovoltaica", "Dimensiona sistema solar on-grid por cidade (HSP), inversor, strings e retorno financeiro", "calculadora-fotovoltaica", "pvs_gui.pyw"),
    ("🔌", "Calculadora Elétrica Residencial", "Bitola do fio, disjuntor, queda de tensão e consumo (tabelas NBR 5410)", "calculadora-eletrica-residencial", "ele_gui.pyw"),
    ("📈", "Simulador de Renda Fixa", "CDB, LCI/LCA, Tesouro e poupança com IR e IOF regressivos e equivalência isento", "simulador-renda-fixa", "rfx_gui.pyw"),
    ("🖨️", "Calculadora de Impressão 3D", "Custo e preço da peça, metros↔gramas de filamento e calibração de e-steps/fluxo", "calculadora-impressao-3d", "p3d_gui.pyw"),
    ("📸", "Calculadora de Fotografia", "Profundidade de campo, hiperfocal, exposição/ND, astrofoto, FOV e timelapse", "calculadora-fotografia", "fot_gui.pyw"),
    ("📊", "Visualizador de Ordenação", "Anima Bubble, Quick, Merge, Heap e outros algoritmos com complexidade", "visualizador-ordenacao", "srt_gui.pyw"),
    ("🦠", "Simulador de Epidemias", "Modelos SIR/SEIR/SEIRD com vacinação, R0, pico e imunidade de rebanho", "simulador-epidemias", "sir_gui.pyw"),
    ("🗓️", "Gerador de Escalas de Trabalho", "Escalas 12x36, 24x48, 6x1 e personalizadas com feriados, horas e cobertura", "gerador-escalas-trabalho", "esc_gui.pyw"),
    ("🔋", "Calculadora de Baterias", "Autonomia (Peukert), montagem de pack, banco off-grid e tempo de recarga", "calculadora-baterias", "bat_gui.pyw"),
    ("🎼", "Teoria Musical", "Escalas, acordes, campo harmônico, intervalos e transposição de cifras", "teoria-musical", "esm_gui.pyw"),
    ("🐾", "Dose de Ração & Pet", "Quanto seu cão/gato deve comer por dia (RER/MER), água e idade humana", "pet", "pet_gui.pyw"),
    ("💇", "Cronograma Capilar & Oxidante", "Agenda de hidratação/nutrição/reconstrução + volumes↔% e diluição de oxigenada", "cabelo", "cab_gui.pyw"),
    ("🧳", "Divisor de Despesas em Grupo", "Racha conta: saldo de cada um e menor número de transferências pra acertar", "rateio", "rct_gui.pyw"),
    ("🌡️", "Carta Psicrométrica", "Propriedades do ar úmido, ponto de orvalho, entalpia e HVAC", "carta-psicrometrica", "psi_gui.pyw"),
    ("🤖", "Cinemática Robótica", "Cinemática direta e inversa 2D/3D, Jacobiano, singularidades e trajetórias", "cinematica-robotica", "rob_gui.pyw"),
    ("📒", "Álbum de Figurinhas", "Controle de cromos, trocas e estimativa de pacotes para completar o álbum", "album-figurinhas", "alb_gui.pyw"),
    ("🧭", "Analisador de PATH", "Audita PATH (processo/usuario/maquina): quebradas, duplicadas, vazias e gera versao limpa", "analisador-path", "pth_gui.pyw"),
    ("🔥", "Duração do Botijão", "Consumo por queimador, dias do P13/P45, previsão de troca e comparação com gás encanado", "botijao-gas", "gas_gui.pyw"),
    ("✈️", "Aerodinâmica, Sustentação & Arrasto", "Mecânica de voo, modelo ISA, polar de arrasto, razão de planeio L/D, estol e potência requerida", "calculadora-aerodinamica-arrasto-sustentacao", "aer_gui.pyw"),
    ("🔐", "Calculadora chmod", "Octal ↔ rwx, setuid/setgid/sticky, umask e notação relativa (u+x, g-w)", "calculadora-chmod", "rwx_gui.pyw"),
    ("🏊", "Calculadora de Piscina", "Volume, dosagem de cloro, correção de pH/alcalinidade e tempo de filtragem", "calculadora-piscina", "psc_gui.pyw"),
    ("☀️", "Posição Solar & Algoritmo SPA", "Algoritmo SPA, elevação, azimute, declinação, equação do tempo, massa de ar e irradiância…", "calculadora-posicao-solar-astronomia", "spa_gui.pyw"),
    ("🌊", "Vazão em Placa de Orifício (ISO 5167)", "Medição de vazão por pressão diferencial ISO 5167-2, Cd Reader-Harris, Reynolds e perda…", "calculadora-vazao-placa-orificio", "orf_gui.pyw"),
    ("🚕", "Carro Próprio ou Aplicativo", "Custo mensal real do carro vs app e transporte público, com ponto de equilíbrio", "carro-ou-app", "uba_gui.pyw"),
    ("🪱", "Compostagem Caseira", "Mistura C:N, volume da composteira, tempo e checklist de problemas", "compostagem", "cmp_gui.pyw"),
    ("🔀", "Conversor de Finais de Linha", "Detecta e converte CRLF ↔ LF ↔ CR em texto, arquivo ou pasta em lote", "conversor-finais-linha", "eol_gui.pyw"),
    ("🥫", "Despensa e Validades", "Itens com validade, PEPS, o que consumir primeiro e lista de reposição", "despensa-validade", "dsp_gui.pyw"),
    ("📡", "Editor de Hosts por Linhas", "Lista entradas do hosts, liga/desliga linhas, adiciona hosts e salva com UAC", "editor-hosts-linhas", "hst_gui.pyw"),
    ("🛡️", "Código de Hamming & ECC (SEC-DED)", "Correção de erro Hamming(7,4) e SEC-DED(8,4), matriz geradora, paridade, síndrome e canal com…", "estudio-codigo-hamming-ecc", "ham_gui.pyw"),
    ("🫖", "Fermentados Caseiros", "Receitas e cronograma de kombucha, chucrute, kefir e iogurte", "fermentados-caseiros", "kmb_gui.pyw"),
    ("🎂", "Conversor de Formas de Bolo", "Converte área/volume entre formas e escala a receita e o tempo de forno", "formas-bolo", "bol_gui.pyw"),
    ("📄", "Formatador YAML / TOML", "Formata e valida YAML/TOML e converte entre YAML, TOML e JSON", "formatador-yaml-toml", "yml_gui.pyw"),
    ("🧺", "Guia de Lavanderia", "Tira-manchas por tecido, dosagem de sabão e temperatura/centrifugação", "guia-lavanderia", "lvd_gui.pyw"),
    ("🥕", "Introdução Alimentar do Bebê", "Idade, fase, cardápio semanal, registro de ofertas e alimentos a evitar", "introducao-alimentar", "iab_gui.pyw"),
    ("🧹", "Limpa Temp", "Varre pastas TEMP do Windows por idade/tamanho, mostra previa e apaga com relatorio", "limpa-temp", "tmp_gui.pyw"),
    ("🗑️", "Lixeira do Windows", "Lista, restaura, exclui permanente, esvazia e envia arquivos para a lixeira", "lixeira-windows", "rec_gui.pyw"),
    ("📚", "Meta de Leitura", "Livros, meta anual, páginas por dia, ritmo e previsão de término", "meta-leitura", "lei_gui.pyw"),
    ("🎄", "Orçamento de Natal", "Presentes por pessoa, ceia, divisão do 13º e o que falta comprar", "orcamento-natal", "ntl_gui.pyw"),
    ("⚽", "Organizador de Pelada", "Times equilibrados, quem ganha fica, placar, artilharia e rateio da quadra", "pelada-futebol", "pld_gui.pyw"),
    ("🎯", "Plano de Estudos para Concurso", "Distribui horas por peso e domínio, grade semanal, revisões e contagem regressiva", "plano-concurso", "ccs_gui.pyw"),
    ("🏢", "Rateio de Condomínio", "Rateio por fração ou igualitário, fundo de reserva, multa/juros e chamada de capital", "rateio-condominio", "cnd_gui.pyw"),
    ("🏠", "Reajuste de Aluguel", "Reajuste por índice, proporcional, multa rescisória e caução", "reajuste-aluguel", "alu_gui.pyw"),
    ("🚸", "Rodízio de Carona", "Escala justa de motoristas, custo de combustível e saldo entre famílias", "rodizio-carona", "crp_gui.pyw"),
    ("🧴", "Rotina de Skincare", "Monta rotina manhã/noite, conflitos de ativos, introdução gradual e duração do frasco", "rotina-skincare", "skn_gui.pyw"),
    ("🧼", "Sabonetes e Velas Artesanais", "Receita a frio com NaOH, cera/essência/pavio para velas e custo por unidade", "sabonetes-velas", "sab_gui.pyw"),
    ("🏋️", "Treino de Academia", "1RM, tabela de cargas, progressão, anilhas por lado e volume semanal", "treino-academia", "rmx_gui.pyw"),
    ("📋", "Gerador de .gitignore", "Templates offline (Python/Node/Windows…), merge, detecção de stack e exportação.", "gerador-gitignore", "gig_gui.pyw"),
    ("🐣", "Chocolate e Ovos de Páscoa", "Temperagem, rendimento de ovos, recheio e preço de venda", "chocolate-pascoa", "pcs_gui.pyw"),
    ("🐷", "Desafio da Poupança", "Desafio 52 semanas, envelopes ou meta com data", "desafio-poupanca", "cof_gui.pyw"),
    ("🩸", "Diário de Pressão e Glicemia", "Registros de pressão e glicemia, médias e CSV para o médico", "diario-pressao", "prs_gui.pyw"),
    ("🍗", "Tempo de Forno de Carnes", "Tempo, temperatura e horário para assar carnes", "forno-carnes", "asd_gui.pyw"),
    ("✍️", "Jogo Stop (Adedonha)", "Sorteio de letra, cronômetro e pontuação do Stop", "jogo-stop", "stp_gui.pyw"),
    ("🔧", "Manutenção da Casa", "Agenda de manutenções periódicas da casa com atrasadas", "manutencao-casa", "mnt_gui.pyw"),
    ("🧵", "Metragem de Tecido", "Calcula metros de tecido para cortina, toalha, almofada e lençol", "metragem-costura", "cst_gui.pyw"),
    ("📜", "Papel de Parede e Revestimentos", "Rolos de papel de parede e adesivo/placas por m²", "papel-parede", "ppd_gui.pyw"),
    ("📺", "Tamanho Ideal de TV", "Diagonal ideal pela distância, resolução e altura de instalação", "tamanho-tv", "tvd_gui.pyw"),
    ("🍷", "Harmonização de Vinhos e Queijos", "Sugere vinhos para queijos, quantidade e temperatura", "vinhos-queijos", "vnh_gui.pyw"),
    ("🔤", "Conversor de Encoding", "Detecta e converte UTF-8/Latin-1/CP1252/UTF-16 (BOM), corrige mojibake e lote em pasta", "conversor-encoding", "enc_gui.pyw"),
    ("↔️", "Conversor de Indentação", "Detecta e converte tabs ↔ espaços em texto ou pasta de código", "conversor-indentacao", "ind_gui.pyw"),
    ("⚙️", "Gerador de .editorconfig", "Presets por stack (Python/Node/Go…), merge, validação e exportação de .editorconfig", "gerador-editorconfig", "edc_gui.pyw"),
    ("🧹", "Normalizador de Nomes de Arquivo", "Remove acentos, gera nomes ASCII seguros e renomeia em lote com prévia", "normalizador-nomes", "nfn_gui.pyw"),
    ("🧪", "Reologia de Fluidos Não Newtonianos", "Modelos Ostwald-de Waele, Bingham e Casson, reogramas e escoamento em duto com núcleo rígido…", "reologia-fluidos", "reo_gui.pyw"),
    ("⚛️", "Simulador de Tunelamento Quântico 1D", "Equação de Schrödinger 1D, coeficientes de transmissão/reflexão e densidade de probabilidade", "tunelamento-quantico", "tun_gui.pyw"),
    ("☀️", "Aquecedor Solar de Água", "Dimensiona boiler e coletores, estima economia frente ao chuveiro elétrico e payback", "aquecedor-solar", "aqs_gui.pyw"),
    ("🍓", "Calendário de Safra", "Frutas, legumes e verduras da época no Brasil, o que está barato e lista de compras", "calendario-safra", "sfr_gui.pyw"),
    ("🥗", "Calorias da Receita", "Tabela nutricional da receita a partir dos ingredientes, totais e por porção", "calorias-receita", "kcr_gui.pyw"),
    ("🧸", "Casa Segura para o Bebê", "Checklist de prevenção por cômodo e fase do bebê, progresso e prioridades", "casa-segura-bebe", "sgb_gui.pyw"),
    ("🎁", "Chá de Bebê, Panela e Casa Nova", "Sugestão de presentes, fraldas, brincadeiras e comidas para chá de bebê, panela e casa nova", "chas-presentes", "cha_gui.pyw"),
    ("🌺", "Cuidados com Orquídeas", "Luz, rega, adubação e diagnóstico por gênero de orquídea, com registro das plantas", "cuidados-orquideas", "orq_gui.pyw"),
    ("🌽", "Festa Junina", "Quantidades de comidas típicas, receita de quentão, fichas das barracas e sorteio da quadrilha", "festa-junina", "jun_gui.pyw"),
    ("🛠️", "Orçamento de Reforma", "Itens por cômodo, reserva para imprevistos, comparação de orçamentos e cronograma de pagamento", "orcamento-reforma", "rfm_gui.pyw"),
    ("🔲", "Placar de Dominó", "Placar de dominó com modos por pedras ou batidas, meta, histórico e contagem de pedras", "placar-domino", "dmn_gui.pyw"),
    ("❓", "Quiz da Família", "Perguntas por categoria, cronômetro, pontuação com bônus de velocidade e placar", "quiz-familia", "qzf_gui.pyw"),
    ("🎉", "Aniversários da Família", "datas, idade que vai fazer, contagem regressiva, próximos 30 dias e signo", "aniversarios-familia", "anv_gui.pyw"),
    ("🥐", "Cardápio de Café da Manhã", "cardápio semanal por grupo, quantidades por pessoa e lista de compras", "cafe-da-manha", "cfm_gui.pyw"),
    ("🛞", "Calibragem e Rodízio de Pneus", "pressão por carga/viagem, psi/bar/kPa, rodízio, TWI e DOT", "calibragem-pneus", "pnu_gui.pyw"),
    ("📉", "Juros do Cartão Rotativo", "rotativo vs parcelamento vs mínimo, CET, IOF e tempo para quitar", "cartao-rotativo", "rot_gui.pyw"),
    ("⏱️", "Comparador de Timestamps", "Compara mtime/atime/ctime, lista pasta por data, touch e copia mtime entre arquivos.", "comparador-timestamps", "mtm_gui.pyw"),
    ("💡", "Rateio da Conta de Luz", "divide a conta entre moradores por aparelhos e horas (kWh), parte fixa e bandeira", "conta-luz-republica", "rlz_gui.pyw"),
    ("📊", "Contador de Linhas de Código", "Conta código, comentários e vazios por linguagem (estilo cloc).", "contador-linhas-codigo", "clc_gui.pyw"),
    ("🛣️", "Conversor de Path", "Windows ↔ POSIX ↔ WSL ↔ Git Bash ↔ file://.", "conversor-path", "wup_gui.pyw"),
    ("🏎️", "Dinâmica Veicular & Pneu de Pacejka", "Modelo de bicicleta, gradiente de subesterço, velocidade crítica/característica e Fórmula Mágica de Pacejka", "dinamica-veicular-pacejka", "dnv_gui.pyw"),
    ("🙏", "Dízimo e Doações", "percentual sobre a renda, metas, histórico mensal e total para o IR", "dizimo-doacoes", "dzm_gui.pyw"),
    ("🎈", "Planejador de Festa Infantil", "convidados, salgados, doces, bolo, lembrancinhas, cronograma e orçamento", "festa-infantil", "fsi_gui.pyw"),
    ("📎", "Gerador de .gitattributes", "Presets de EOL, binários, linguagens, export-ignore e diff drivers.", "gerador-gitattributes", "gat_gui.pyw"),
    ("🛠️", "Gerador de Makefile", "Templates de Makefile para Python, Node, C, Go e Docker.", "gerador-makefile", "mkf_gui.pyw"),
    ("🔗", "Gerador de Slug", "Texto→slug URL/filename, lote, unicidade e âncoras Markdown.", "gerador-slug", "slg_gui.pyw"),
    ("🌲", "Gerador de Tree", "Árvore ASCII/Markdown de diretórios pra colar no README.", "gerador-tree", "trd_gui.pyw"),
    ("📜", "Inspetor de Shebang", "Detecta #! em scripts, aponta CRLF quebrado, sugere interpretador e aplica shebang.", "inspetor-shebang", "shb_gui.pyw"),
    ("⚙️", "Simulador de Ciclos Termodinâmicos", "Ciclos de Carnot, Otto, Diesel, Brayton e Rankine, diagramas P-v e T-s, rendimento e trabalho líquido", "simulador-ciclos-termodinamicos", "ctm_gui.pyw"),
    ("🌙", "Diário de Sono do Bebê", "registra sonecas e noite, total vs recomendado por idade, janelas de vigília e próxima soneca", "sono-bebe", "sbb_gui.pyw"),
    ("🛢️", "Troca de Óleo do Carro", "intervalo por km e tempo, litros, filtros e próxima troca", "troca-oleo", "olo_gui.pyw"),
    ("💉", "Carteira de Vacinas do Pet", "cães e gatos, calendário de vacinas, vermífugo e antipulgas, próximas doses e atrasadas", "vacinas-pet", "vcp_gui.pyw"),
    ("🧾", "Validador de .env", "Valida .env, detecta duplicatas/segredos, diff com .env.example e exporta JSON.", "validador-dotenv", "den_gui.pyw"),
    ("🛏️", "Divisão de Aluguel por Quarto", "divide aluguel e contas por área do quarto, banheiro privativo, vaga e áreas comuns, com pesos ajustáveis.", "aluguel-quartos", "alq_gui.pyw"),
    ("⏰", "Banco de Horas", "batidas de ponto por dia, jornada contratual, saldo diário e acumulado, horas extras 50%/100% e adicional noturno.", "banco-horas", "bhr_gui.pyw"),
    ("🚶", "Calorias da Atividade", "gasto calórico por MET (caminhada, corrida, bike, natação etc.) pelo peso e tempo, passos para km e meta semanal.", "calorias-atividade", "met_gui.pyw"),
    ("💊", "Cartela do Anticoncepcional", "cartelas 21/24/28 dias e contínuo, pausa, dia de hoje na cartela, esquecimento (orientação geral informativa) e próxima cartela.", "cartela-anticoncepcional", "acp_gui.pyw"),
    ("🧉", "Chimarrão e Tererê", "temperatura ideal da água, erva por cuia, rendimento da garrafa térmica, consumo mensal de erva e custo.", "chimarrao-terere", "chi_gui.pyw"),
    ("📝", "Contador de Palavras", "Conta chars, palavras, linhas, parágrafos e tempo de leitura.", "contador-palavras", "wdc_gui.pyw"),
    ("📄", "Diff de Texto", "Diff unified/context/ndiff entre dois textos com similaridade.", "diff-texto", "tdf_gui.pyw"),
    ("🏥", "Escala de Plantão", "gera escalas 12x36, 24x48, 6x1 e 5x2 por pessoa, calendário do mês, horas por pessoa e feriados trabalhados.", "escala-plantao", "plt_gui.pyw"),
    ("📐", "Formatador de Tamanho", "Converte bytes ↔ KiB/MiB/GiB e unidades SI (KB/MB/GB).", "formatador-tamanho", "hsz_gui.pyw"),
    ("📦", "Frete e Embalagem para Vender Online", "peso cúbico vs real, caixa ideal, custo de embalagem, taxa do marketplace e preço mínimo com margem.", "frete-vendas", "frv_gui.pyw"),
    ("🐳", "Gerador de .dockerignore", "Templates offline de .dockerignore (Base/Python/Node/Dev/Tests).", "gerador-dockerignore", "dik_gui.pyw"),
    ("📜", "Gerador de LICENSE", "Gera LICENSE MIT/Apache/BSD/GPL/Unlicense com autor e ano.", "gerador-license", "lic_gui.pyw"),
    ("📦", "Gerador de requirements.txt", "Varre imports Python, ignora stdlib e gera requirements.txt.", "gerador-requirements", "req_gui.pyw"),
    ("🧱", "Drywall e Forro de Gesso", "placas, montantes, guias, parafusos, fita e massa por m² de parede ou forro, com perdas.", "gesso-drywall", "dry_gui.pyw"),
    ("🚭", "Parar de Fumar", "dias sem fumar, cigarros evitados, dinheiro economizado, marcos de saúde por tempo e metas.", "parar-fumar", "fum_gui.pyw"),
    ("🕵️", "Scanner de Segredos", "Varre código por API keys, tokens, JWT e chaves privadas.", "scanner-segredos", "sek_gui.pyw"),
    ("⚗️", "Simulador de Reatores Químicos", "Balanço molar de CSTR, PFR e Batelada, cinética de Arrhenius, gráfico de Levenspiel e perfis de concentração", "simulador-reatores-quimicos", "rea_gui.pyw"),
    ("🪪", "Vencimento de Documentos", "CNH, RG, passaporte, título, CRLV, seguros e garantias, dias para vencer, alertas 30/60/90 dias.", "vencimento-documentos", "vdc_gui.pyw"),
    ("📌", "Analisador de TODO/FIXME", "Varre código por TODO, FIXME, XXX, HACK, BUG, NOTE e OPTIMIZE.", "analisador-todo", "tdo_gui.pyw"),
    ("🌊", "Canais Abertos (Manning) & Ressalto Hidráulico", "Escoamento em canais abertos pela Equação de Manning, Froude, energia específica e ressalto de Bélanger", "calculadora-canais-abertos-manning", "can_gui.pyw"),
    ("🚧", "Cerca e Alambrado", "Perímetro, mourões pelo espaçamento, rolos de tela, fios de arame, cantos/esticadores e custo.", "cerca-alambrado", "cer_gui.pyw"),
    ("🎀", "Chá Revelação", "Convidados, palpites menino/menina com placar, bolão, comidas/lembrancinhas e checklist.", "cha-revelacao", "rev_gui.pyw"),
    ("🌧️", "Cisterna de Água de Chuva", "Captação pelo telhado e chuva média, volume ideal, economia de água e meses de autonomia.", "cisterna-chuva", "cis_gui.pyw"),
    ("🔢", "Comparador SemVer", "Compara, faz bump e testa ranges SemVer (^ ~ >=).", "comparador-semver", "smv_gui.pyw"),
    ("🥚", "Tempo de Cozimento", "Ovos, arroz, feijão na pressão, grãos, massas e legumes, com proporção de água e timer.", "cozimento-alimentos", "coz_gui.pyw"),
    ("🎣", "Diário de Pesca", "Registra pescarias (local, espécie, peso, isca, lua, maré), recordes e melhor isca por espécie.", "diario-pesca", "pes_gui.pyw"),
    ("🤝", "Empréstimos de Objetos", "O que você emprestou ou pegou emprestado, com quem, data, prazo de devolução e atrasados.", "emprestimos-objetos", "emp_gui.pyw"),
    ("📰", "Gerador de CHANGELOG", "Keep a Changelog: novas versões semver e prévia/exportação do CHANGELOG.md.", "gerador-changelog", "chg_gui.pyw"),
    ("📦", "Gerador de .npmignore", "Templates offline de .npmignore (Base/testes/docs/TypeScript), merge e exportação.", "gerador-npmignore", "nmi_gui.pyw"),
    ("🪝", "Gerador de pre-commit", "Presets de .pre-commit-config.yaml (Basico/Python/JS/Seguranca).", "gerador-pre-commit", "pcc_gui.pyw"),
    ("🌿", "Grama em Placas e Sementes", "m² de grama em placas ou sementes por espécie, terra, adubo e rega inicial.", "grama-jardim", "grm_gui.pyw"),
    ("🎛️", "Laboratório de Filtros Digitais (DSP)", "Síntese de filtros IIR, resposta em frequência em dB, diagrama de polos/zeros no plano Z e estabilidade BIBO", "laboratorio-filtros-digitais", "fdt_gui.pyw"),
    ("👁️", "Lentes de Contato", "Troca diária/quinzenal/mensal por olho, dias de uso, próxima troca, estoque de caixas e custo mensal.", "lentes-contato", "lct_gui.pyw"),
    ("🪵", "Piso Vinílico e Laminado", "Réguas por cômodo com perda por paginação, caixas, manta, rodapé em barras e cantoneiras.", "piso-vinilico", "vin_gui.pyw"),
    ("📐", "Complexidade Ciclomatica", "McCabe via AST em Python e heuristica por tokens; analisa buffer ou pasta.", "complexidade-ciclomatica", "cyc_gui.pyw"),
    ("🏅", "Gerador de Badges", "Gera markdown de badges shields.io com presets e custom label/message/cor.", "gerador-badges", "bdg_gui.pyw"),
    ("✂️", "Removedor de Comentarios", "Remove comentarios Python/# // /* */ HTML preservando strings (heuristico).", "removedor-comentarios", "scm_gui.pyw"),
    ("👯", "Funcoes Duplicadas", "Detecta funcoes Python com mesmo nome ou corpo AST identico.", "analisador-funcoes-duplicadas", "dfn_gui.pyw"),
    ("🧹", "Imports Nao Usados", "Heuristica AST de imports/from Python nao referenciados no arquivo.", "analisador-imports-nao-usados", "udi_gui.pyw"),
    ("📦", "Analisador de package-lock", "Conta pacotes/deps no package-lock.json e aponta nomes duplicados.", "analisador-package-lock", "plk_gui.pyw"),
    ("🧊", "Analisador pip freeze", "Compara requirements.txt com pip freeze: pins divergentes e pacotes so de um lado.", "analisador-pip-freeze", "drf_gui.pyw"),
    ("📏", "Tamanho de Funcoes", "Ranking de defs Python por linhas (LOC) com filtro minimo.", "analisador-tamanho-funcoes", "fsz_gui.pyw"),
    ("🕒", "Arquivos Recentes", "Lista arquivos modificados nas ultimas N horas por mtime.", "arquivos-recentes", "mtr_gui.pyw"),
    ("🌲", "Arvore de Diretorios", "Tree ASCII com profundidade, ocultos e so pastas; ignora .git/node_modules.", "arvore-diretorios", "trv_gui.pyw"),
    ("🌬️", "Energia Eólica, Aerogeradores & Limite de Betz", "Curva de potência P(v) em 4 regiões, Limite de Betz (59.3%), TSR, coeficiente Cp e produção anual AEP de Weibull", "calculadora-energia-eolica-aerogerador", "eoc_gui.pyw"),
    ("📡", "Guias de Onda Retangulares & Micro-ondas", "Frequências de corte TE/TM, modo dominante TE10, dispersão, impedância de onda e mapa de campo", "calculadora-guia-ondas-retangular", "gdo_gui.pyw"),
    ("☢️", "Cinética de Decaimento Nuclear e Bateman", "Equações de Bateman, equilíbrio secular e transitório, atividade em Bq/Ci e curvas de decaimento", "cinetica-decaimento-nuclear-bateman", "dcn_gui.pyw"),
    ("⬜", "Compactador de Whitespace", "Tabs→espacos, trim a direita e colapso de linhas em branco.", "compactador-whitespace", "wsp_gui.pyw"),
    ("📏", "Caminhos Longos", "Detecta paths longos (alerta antes do MAX_PATH).", "detector-caminhos-longos", "lng_gui.pyw"),
    ("🔠", "Encoding Misto", "Detecta UTF-8 BOM, Latin-1 e binario em textos do projeto.", "detector-encoding-misto", "encm_gui.pyw"),
    ("↵", "Newline final", "Detecta textos sem newline no final e corrige em lote.", "detector-newline-final", "nln_gui.pyw"),
    ("🔗", "Symlinks Quebrados", "Varre pasta e lista symlinks cujo alvo nao existe.", "detector-symlinks-quebrados", "syb_gui.pyw"),
    ("⚙️", "Simulador de Engrenagens Planetárias e Epicicloidais", "Cinemática de Willis, coaxialidade, alavanca de Kutzbach e divisor híbrido Prius", "engrenagens-planetarias-epicicloidais", "epi_gui.pyw"),
    ("🔤", "Extrator de Strings Binario", "Extrai strings ASCII e UTF-16LE de arquivos binarios com offset.", "extrator-strings-binario", "xtr_gui.pyw"),
    ("🛡️", "Gerador de .bandit", "Presets Bandit YAML (Basico, Strict, Django-ish).", "gerador-bandit-yaml", "bdt_gui.pyw"),
    ("⬛", "Gerador Black", "Snippets [tool.black] para pyproject.toml.", "gerador-black", "blk_gui.pyw"),
    ("🥟", "Gerador bunfig.toml", "Presets Bun bunfig.toml.", "gerador-bunfig", "bun_gui.pyw"),
    ("📦", "Gerador Cargo.toml", "Presets Cargo.toml Rust (bin, lib, clap).", "gerador-cargo-toml", "cgo_gui.pyw"),
    ("🛠️", "Gerador de .clang-format", "Presets clang-format (LLVM, Google, Mozilla, WebKit, Custom).", "gerador-clang-format", "clf_gui.pyw"),
    ("🧹", "Gerador .clang-tidy", "Presets .clang-tidy (Basico, Modernize, Performance).", "gerador-clang-tidy", "cty_gui.pyw"),
    ("🧱", "Gerador CMakeLists", "Presets CMakeLists.txt (exe C++, lib+exe, C+tests).", "gerador-cmakelists", "cmk_gui.pyw"),
    ("👥", "Gerador CODEOWNERS", "Templates GitHub CODEOWNERS (basico, monorepo, security).", "gerador-codeowners", "own_gui.pyw"),
    ("✍️", "Gerador Commitizen", "Presets .cz.toml / tool.commitizen conventional commits.", "gerador-commitizen", "czc_gui.pyw"),
    ("📊", "Gerador de .coveragerc", "Presets coverage.py (Basico, Strict 90, XML CI).", "gerador-coveragerc", "cov_gui.pyw"),
    ("🚫", "Gerador de .eslintignore", "Templates offline de .eslintignore (Base, Next/Nuxt, testes, configs).", "gerador-eslintignore", "esi_gui.pyw"),
    ("❄️", "Gerador de .flake8", "Presets flake8 (Basico, Strict, Django).", "gerador-flake8", "flk_gui.pyw"),
    ("⚙️", "Gerador de GitHub Actions", "Templates YAML offline de workflows (Python CI, Node, Release, Lint).", "gerador-github-actions", "gha_gui.pyw"),
    ("📚", "Gerador de .isort.cfg", "Presets isort (Black, src, Google).", "gerador-isort-cfg", "iso_gui.pyw"),
    ("📖", "Gerador de man page", "Gera pagina man em troff (.TH/.SH/.TP) com synopsis e opcoes.", "gerador-manpage", "man_gui.pyw"),
    ("⚙️", "Gerador meson.build", "Presets Meson (C, C++, lib+exe).", "gerador-meson", "msn_gui.pyw"),
    ("🔬", "Gerador de mypy.ini", "Presets mypy.ini (Basico, Strict, Django-ish).", "gerador-mypy-ini", "myp_gui.pyw"),
    ("📟", "Gerador de .npmrc", "Presets de .npmrc (registry, save-exact, verdaccio, proxy corporativo).", "gerador-npmrc", "nrc_gui.pyw"),
    ("🟢", "Gerador de .nvmrc", "Gera .nvmrc ou .node-version com versao Node (LTS/numeros).", "gerador-nvmrc", "nvm_gui.pyw"),
    ("📜", "Gerador Poetry", "Presets pyproject.toml Poetry (app, lib+extras, CLI) com nome do projeto.", "gerador-poetry-pyproject", "poe_gui.pyw"),
    ("✨", "Gerador de .prettierrc", "Presets Prettier offline em JSON/YAML (Padrao, Airbnb-ish, Compacto, Strict).", "gerador-prettierrc", "ptt_gui.pyw"),
    ("🐍", "Gerador de .pylintrc", "Presets pylint (Basico, Strict, Django).", "gerador-pylint", "pyl_gui.pyw"),
    ("🧪", "Gerador de pytest.ini", "Presets pytest.ini (Basico, coverage, markers).", "gerador-pytest-ini", "pti_gui.pyw"),
    ("🐦", "Gerador de ruff.toml", "Presets Ruff lint/format (Basico, Strict, Minimal).", "gerador-ruff-toml", "ruf_gui.pyw"),
    ("🧰", "Gerador de setup.cfg", "Gera setup.cfg setuptools com metadata, pytest e flake8 opcionais.", "gerador-setup-cfg", "scf_gui.pyw"),
    ("🏷️", "Gerador setuptools_scm", "Snippets de versao dinamica via git (setuptools_scm).", "gerador-setuptools-scm", "ssc_gui.pyw"),
    ("🔄", "Gerador .stignore", "Templates Syncthing .stignore (Basico, Dev, Media).", "gerador-syncthingignore", "stg_gui.pyw"),
    ("🧪", "Gerador de tox.ini", "Presets tox.ini (multi-py, pytest+ruff, docs mkdocs).", "gerador-tox-ini", "tox_gui.pyw"),
    ("🧶", "Gerador .yarnrc.yml", "Presets Yarn Berry (.yarnrc.yml).", "gerador-yarnrc", "yrn_gui.pyw"),
    ("📤", "Inspetor de Exports DLL", "Le a Export Directory PE32/PE32+ de DLL/EXE e lista ordinal/RVA/nome.", "inspetor-dll-exports", "dex_gui.pyw"),
    ("🐧", "Inspetor ELF", "Le cabecalho ELF32/ELF64 (tipo, machine, entry, PH/SH).", "inspetor-elf", "elf_gui.pyw"),
    ("🗜️", "Inspetor ZIP", "Lista entradas do ZIP com tamanhos, metodo e taxa de compressao.", "inspetor-zip-central", "zcd_gui.pyw"),
    ("🧹", "Limpeza de __pycache__", "Varre e apaga __pycache__, *.pyc e caches pytest/mypy/ruff.", "limpeza-pycache", "pyc_gui.pyw"),
    ("🔗", "Listador de Hardlinks", "Agrupa arquivos com mesmo inode (st_nlink>1) numa pasta.", "listador-hardlinks", "hlk_gui.pyw"),
    ("🕳️", "Localizador de Arquivos Vazios", "Lista arquivos 0 bytes e pastas vazias; apaga arquivos vazios sob confirmacao.", "localizador-arquivos-vazios", "efn_gui.pyw"),
    ("📐", "Simulador de Mecanismo de Quatro Barras", "Criterio de Grashof, equacao de Freudenstein, angulo de transmissao e curva do acoplador", "simulador-mecanismo-quatro-barras", "mqb_gui.pyw"),
    ("🐘", "Top Arquivos Grandes", "Ranking dos N maiores arquivos da pasta.", "top-arquivos-grandes", "big_gui.pyw"),
    ("🧾", "Validador TOML", "Valida TOML via tomllib, resume chaves e exporta JSON.", "validador-toml", "tml_gui.pyw"),
    ("🔄", "Imports Circulares", "Detecta ciclos no grafo de imports Python de um projeto.", "analisador-imports-circulares", "icl_gui.pyw"),
    ("🍎", "Inspetor Mach-O", "Le magic/header Mach-O 32/64 e FAT.", "inspetor-macho", "mac_gui.pyw"),
    ("📋", "Gerador justfile", "Presets justfile (Python, Node, Docker).", "gerador-justfile", "jst_gui.pyw"),
    ("🚀", "Gerador Procfile", "Presets Procfile (Django, Flask, Node, worker).", "gerador-procfile", "pfl_gui.pyw"),
    ("✅", "Gerador Taskfile.yml", "Presets Taskfile.yml (Basico, Python, Docker).", "gerador-taskfile", "tsk_gui.pyw"),
    ("📦", "Gerador Vagrantfile", "Presets Vagrantfile (Ubuntu, Docker, synced).", "gerador-vagrantfile", "vag_gui.pyw"),
    ("🐍", "Gerador .python-version", "Gera .python-version para pyenv com versoes comuns.", "gerador-python-version", "pyv_gui.pyw"),
    ("📥", "Inspetor PE Imports", "Lista DLLs e funcoes importadas de EXE/DLL (tabela de importacao PE).", "inspetor-pe-imports", "pei_gui.pyw"),
    ("🌍", "Gerador Earthfile", "Presets Earthfile (Go, Node, Python).", "gerador-earthfile", "ear_gui.pyw"),
    ("🧰", "Gerador .tool-versions", "Presets asdf .tool-versions.", "gerador-tool-versions", "tvs_gui.pyw"),
    ("📂", "Gerador .envrc", "Presets direnv .envrc (venv, node, asdf, nix).", "gerador-envrc", "drc_gui.pyw"),
    ("🍺", "Gerador Brewfile", "Presets Homebrew Brewfile.", "gerador-brewfile", "bfi_gui.pyw"),
    ("🧱", "Gerador Makefile nmake", "Presets Makefile para nmake/cl.exe Windows.", "gerador-nmake", "nmk_gui.pyw"),
    ("📎", "Listador de Dependencias PE", "Lista DLLs unicas importadas por EXE/DLL (dependencias PE).", "listador-deps-pe", "dep_gui.pyw"),
    ("📐", "Gerador pyrightconfig.json", "Presets pyrightconfig.json (Basico, Strict, Monorepo).", "gerador-pyrightconfig", "pyr_gui.pyw"),
    ("🤖", "Gerador Dependabot", "Presets .github/dependabot.yml (pip, npm, github-actions, docker).", "gerador-dependabot", "dpb_gui.pyw"),
    ("🔄", "Gerador Renovate", "Presets renovate.json (Basico, Grouped, Automerge patch).", "gerador-renovate", "rnv_gui.pyw"),
    ("🧠", "Gerador .clangd", "Presets .clangd (Basico, Compile flags, Query driver).", "gerador-clangd", "cld_gui.pyw"),
    ("📝", "Gerador .markdownlint", "Presets .markdownlint.json / .markdownlint.yaml.", "gerador-markdownlint", "mdl_gui.pyw"),
    ("▶️", "Gerador VS Code launch.json", "Presets .vscode/launch.json (Python, Node, C++, Chrome).", "gerador-vscode-launch", "vsc_gui.pyw"),
    ("🧾", "Gerador .yamllint", "Presets .yamllint (Basico, Strict, Relaxed).", "gerador-yamllint", "ylt_gui.pyw"),
    ("🐳", "Gerador .hadolint.yaml", "Presets .hadolint.yaml (Basico, Strict, CI).", "gerador-hadolint", "hdc_gui.pyw"),
    ("🗃️", "Gerador .sqlfluff", "Presets .sqlfluff (ANSI, Postgres, BigQuery).", "gerador-sqlfluff", "sfl_gui.pyw"),
    ("🚀", "Gerador .goreleaser", "Presets .goreleaser.yaml (Binario, Multi-OS, Docker).", "gerador-goreleaser", "grr_gui.pyw"),
    ("📦", "Gerador Dev Container", "Presets .devcontainer/devcontainer.json (Python, Node, Go).", "gerador-devcontainer", "dvc_gui.pyw"),
    ("⚙️", "Gerador VS Code tasks.json", "Presets .vscode/tasks.json (Python, Node, Make, Docker).", "gerador-vscode-tasks", "vst_gui.pyw"),
    ("🧪", "Gerador noxfile.py", "Presets noxfile.py (lint, tests, docs).", "gerador-noxfile", "nox_gui.pyw"),
    ("🪟", "Gerador manifesto Winget", "Presets YAML de manifesto winget (installer + locale).", "gerador-winget", "wgm_gui.pyw"),
    ("🍨", "Gerador manifesto Scoop", "Presets JSON de app Scoop (url, hash, bin, shortcuts).", "gerador-scoop", "sco_gui.pyw"),
    ("🍫", "Gerador Chocolatey nuspec", "Presets .nuspec Chocolatey (Basico, Com deps, Portable).", "gerador-chocolatey-nuspec", "chc_gui.pyw"),
    ("📌", "Gerador tasks.py (Invoke)", "Presets tasks.py do Invoke (test, build, release).", "gerador-invoke", "inv_gui.pyw"),
    ("🏷️", "Inspetor PE Version Info", "Extrai FileVersion, ProductVersion e strings de VERSIONINFO.", "inspetor-pe-version", "pev_gui.pyw"),
    ("🧰", "Gerador mise.toml", "Presets mise.toml (Python/Node/Go toolchains).", "gerador-mise", "mse_gui.pyw"),
    ("📦", "Gerador pip.conf", "Presets pip.conf / pip.ini (indice, timeout, trusted-host).", "gerador-pip-conf", "pcf_gui.pyw"),
    ("🐍", "Gerador .condarc", "Presets .condarc (conda channels, strict, env dirs).", "gerador-condarc", "asc_gui.pyw"),
    ("📥", "Gerador script NSIS", "Presets .nsi (instalador basico, com uninstaller, silent).", "gerador-nsis", "nsi_gui.pyw"),
    ("💿", "Gerador script Inno Setup", "Presets .iss (Basico, Tasks, Portugues).", "gerador-inno-setup", "iss_gui.pyw"),
    ("🏗️", "Gerador Bazel MODULE/BUILD", "Presets MODULE.bazel e BUILD (cc_binary, py_binary).", "gerador-bazel", "bzl_gui.pyw"),
    ("📦", "Gerador WiX", "Presets .wxs WiX Toolset (Product, Fragment, Bundle).", "gerador-wix", "wxi_gui.pyw"),
    ("📱", "Gerador AppxManifest", "Presets AppxManifest.xml (UWP/MSIX basico).", "gerador-appxmanifest", "apx_gui.pyw"),
    ("🐞", "Gerador .lldbinit", "Presets .lldbinit (basico, python, pretty printers).", "gerador-lldbinit", "llb_gui.pyw"),
    ("🪲", "Gerador .gdbinit", "Presets .gdbinit (basico, TUI, pretty printers).", "gerador-gdbinit", "gdb_gui.pyw"),
    ("🎡", "Inspetor de Wheel", "Le METADATA/WHEEL/RECORD de pacotes .whl.", "inspetor-wheel", "whl_gui.pyw"),
    ("🥚", "Inspetor dist-info / egg-info", "Le METADATA/PKG-INFO de pastas .dist-info ou .egg-info.", "inspetor-dist-info", "egg_gui.pyw"),
    ("📨", "Gerador Protobuf", "Presets .proto (mensagem, servico, enums).", "gerador-protobuf", "pbn_gui.pyw"),
    ("🔌", "Gerador gRPC service", "Presets .proto com servico gRPC (unary, stream, health).", "gerador-grpc", "grp_gui.pyw"),
    ("📋", "Gerador CycloneDX SBOM", "Presets SBOM CycloneDX JSON (app, lib, minimal).", "gerador-cyclonedx", "cyd_gui.pyw"),
    ("💎", "Gerador gemspec", "Presets .gemspec RubyGems (basico, com deps, executavel).", "gerador-gemspec", "gem_gui.pyw"),
    ("🪶", "Gerador schema Avro", "Presets Avro JSON Schema (record, enum, union).", "gerador-avro", "avr_gui.pyw"),
    ("📡", "Gerador Thrift IDL", "Presets Apache Thrift IDL (struct, service, enum).", "gerador-thrift", "thf_gui.pyw"),
    ("📜", "Gerador OpenAPI", "Presets OpenAPI 3.1 (CRUD, auth bearer, webhook).", "gerador-openapi", "oas_gui.pyw"),
    ("🟣", "Gerador GraphQL SDL", "Presets GraphQL schema (types, query/mutation, subscription).", "gerador-graphql", "gql_gui.pyw"),
    ("🌊", "Gerador AsyncAPI", "Presets AsyncAPI 3.0 (Kafka, MQTT, WebSocket).", "gerador-asyncapi", "asy_gui.pyw"),
    ("📘", "Gerador RAML", "Presets RAML 1.0 (basico, traits, types).", "gerador-raml", "rml_gui.pyw"),
    ("⚙️", "Gerador Smithy", "Presets Smithy IDL (service, structure, errors).", "gerador-smithy", "smt_gui.pyw"),
    ("🧱", "Gerador FlatBuffers", "Presets .fbs FlatBuffers (table, enum, union).", "gerador-flatbuffers", "fbs_gui.pyw"),
    ("🦀", "Inspetor Cargo.lock", "Lista pacotes name@version de um Cargo.lock.", "inspetor-cargo-lock", "crl_gui.pyw"),
    ("🧶", "Analisador yarn.lock", "Lista entradas versionadas de yarn.lock (v1).", "analisador-yarn-lock", "ylk_gui.pyw"),
    ("📦", "Analisador pnpm-lock.yaml", "Extrai lockfileVersion e pacotes de pnpm-lock.yaml.", "analisador-pnpm-lock", "pnl_gui.pyw"),
    ("🐹", "Inspetor go.sum", "Lista modulos/versoes/hashes de go.sum.", "inspetor-go-sum", "gmd_gui.pyw"),
    ("🎯", "Gerador CUE", "Presets linguagem CUE (schema, defaults, unify).", "gerador-cue", "cue_gui.pyw"),
    ("🔮", "Gerador Dhall", "Presets Dhall (record, union, functions).", "gerador-dhall", "dhl_gui.pyw"),
    ("❄️", "Gerador flake.nix", "Presets Nix flake (devShell, package, overlay).", "gerador-flake-nix", "nix_gui.pyw"),
    ("⎈", "Gerador Helm Chart", "Presets Chart.yaml / values.yaml / deployment template.", "gerador-helm-chart", "hlm_gui.pyw"),
    ("🧩", "Gerador Kustomization", "Presets kustomization.yaml (base, overlay, components).", "gerador-kustomization", "kst_gui.pyw"),
    ("🏛️", "Gerador Terraform", "Presets .tf (provider AWS, modulo local, variables).", "gerador-terraform", "tfr_gui.pyw"),
    ("🟣", "Gerador Pulumi", "Presets Pulumi (Python, TypeScript, YAML).", "gerador-pulumi", "plm_gui.pyw"),
    ("📜", "Gerador Ansible", "Presets playbook/inventory/role Ansible.", "gerador-ansible", "ans_gui.pyw"),
    ("📐", "Calculadora de Propriedades de Seção & Inércia", "Momentos de inércia Ix/Iy, produto Ixy, eixos principais de Steiner, centroide e raio de giração", "calculadora-propriedades-secao-inercia", "sec_gui.pyw"),
    ("🔥", "Condução Térmica Transiente & Fourier", "Número de Biot, Fourier, método das capacidades térmicas globais e perfil de temperatura 1D", "conducao-termica-transiente-fourier", "ftr_gui.pyw"),
    ("🌀", "Projeto & Dimensionamento de Molas Helicoidais", "Fator de Wahl, rigidez elastica k, altura solida, estabilidade a flambagem e fadiga Goodman", "projeto-molas-helicoidais", "mol_gui.pyw"),
    ("🧲", "Simulador de Campo Magnético & Biot-Savart", "Lei de Biot-Savart, bobinas de Helmholtz, perfil axial Bz(z), quadrupolo e raio ciclotrônico de Lorentz", "simulador-campo-magnetico-biot-savart", "bts_gui.pyw"),
    ("📢", "Simulador de Efeito Doppler & Cone de Mach", "Efeito Doppler clássico e relativístico, número de Mach, ângulo de cone de choque e Redshift óptico", "simulador-efeito-doppler-mach", "dop_gui.pyw"),
    ("💧", "Autonomia Caixa d Agua", "Quantos dias a caixa aguenta com o consumo da casa.", "autonomia-caixa-dagua", "cda_gui.pyw"),
    ("🧯", "Calculadora de Botijao de Gas", "Estima duracao e custo diario do botijao conforme uso do fogao.", "calculadora-botijao-gas", "glp_gui.pyw"),
    ("🥗", "Calculadora de Déficit Calórico, TDEE & Macros", "Metabolismo basal (Mifflin/Katch-McArdle), gasto energético diário, déficit seguro, partição de macros e projeção de metas", "calculadora-deficit-calorico", "dfc_gui.pyw"),
    ("🅿️", "Calculadora de Estacionamento", "Valor do estacionamento por horario e tabela (com teto diario).", "calculadora-estacionamento", "est_gui.pyw"),
    ("💧", "Calculadora de Hidratação & Reposição de Eletrólitos", "Taxa de sudorese, reposição de água e sódio pré/intra/pós-treino e índice de calor ACSM", "calculadora-hidratacao-treino", "hdt_gui.pyw"),
    ("🚗", "Calculadora de IPVA", "IPVA pelo valor venal e aliquota tipica da UF (auto/moto, cotas).", "calculadora-ipva", "ipv_gui.pyw"),
    ("💼", "Calculadora de Preço de Hora Freelancer & Diária", "Custo da hora técnica real, ponto de equilíbrio (break-even), ociosidade e orçamento de projetos", "calculadora-preco-freelancer", "phr_gui.pyw"),
    ("🎨", "Rendimento de Tinta", "Litros e latas necessarios para pintar uma area com demaos e perda.", "calculadora-rendimento-tinta", "tnt_gui.pyw"),
    ("🛵", "Taxa e Gorjeta Delivery", "Total do pedido com taxa, gorjeta e cupom.", "calculadora-taxa-delivery", "dlv_gui.pyw"),
    ("🪙", "Calculadora de Troco", "Troco em notas e moedas a partir do total e do valor pago.", "calculadora-troco", "tro_gui.pyw"),
    ("⚖️", "A vista x Parcelado", "Compara compra a vista com desconto versus parcelamento com ou sem juros.", "comparador-avista-parcelado", "dav_gui.pyw"),
    ("⚖️", "Comparador de Propostas CLT vs PJ", "Comparação financeira detalhada com INSS progressivo, IRPF, FGTS, benefícios, Simples Nacional, recesso e break-even", "comparador-clt-pj", "cpj_gui.pyw"),
    ("🏷️", "Comparador Preco Unitario", "Compara R$/un entre embalagens do mercado.", "comparador-preco-unitario", "ppu_gui.pyw"),
    ("🛡️", "Controle de Garantias", "Cadastro de produtos e prazo de garantia.", "controle-garantias", "gar_gui.pyw"),
    ("🧴", "Validade de Cosmeticos", "PAO apos abertura + validade impressa.", "controle-validade-cosmeticos", "csm_gui.pyw"),
    ("💊", "Controle de Validade de Remedios", "Cadastro local de remedios com alerta de vencimento.", "controle-validade-remedios", "rmd_gui.pyw"),
    ("📆", "Dias Uteis de Pagamento", "Dias uteis BR e vencimento no proximo dia util.", "dias-uteis-pagamento", "utl_gui.pyw"),
    ("🚿", "Estimativa de Conta de Agua", "Estima m3/mes pelos habitos e multiplica pela tarifa informada.", "estimativa-conta-agua", "agu_gui.pyw"),
    ("❄️", "Quitador Bola de Neve", "Simula quitar dividas da menor para a maior.", "quitador-dividas-bola-neve", "snw_gui.pyw"),
    ("🏢", "Rateio Condominio por m2", "Divide despesa comum pela area de cada unidade.", "rateio-condominio-m2", "cdn_gui.pyw"),
    ("🏦", "Reserva de Emergencia", "Meta em meses de gasto e aporte mensal para completar.", "reserva-emergencia", "rsv_gui.pyw"),
    ("📅", "Saldo de Prestacoes", "Quanto falta pagar em um parcelamento, com multa opcional.", "saldo-prestacoes", "pst_gui.pyw"),
    ("🛡️", "Calculadora & Planejador da Reserva de Emergência", "Meses ideais por estabilidade profissional, custo essencial de vida, simulação de aportes com CDI e IR regressivo", "calculadora-reserva-emergencia", "rem_gui.pyw"),
    ("🪑", "Calculadora de Ergonomia e Protocolo de Pausas (NR-17)", "Alturas ideais de cadeira, mesa e monitor pela estatura, temporizador 20-20-20 e rotina guiada de alongamentos", "ergonomia-pausas-trabalho", "erg_gui.pyw"),
    ("🏛️", "Estimativa de IPTU", "IPTU pelo valor venal, aliquota, desconto e parcelas.", "calculadora-iptu", "ipt_gui.pyw"),
    ("☕", "Calculadora de Meia-Vida da Cafeína & Sono", "Curva farmacocinética de cafeína no sangue, horário de corte para sono REM e alerta de limite seguro diário", "calculadora-meia-vida-cafeina", "caf_gui.pyw"),
    ("📦", "Atacado × Varejo", "Compara preço unitário com desperdício estimado.", "comparador-atacado-varejo", "atv_gui.pyw"),
    ("📺", "Controle de Assinaturas", "Soma mensal/anual de streaming, apps e assinaturas.", "controle-assinaturas", "ass_gui.pyw"),
    ("🧹", "Custo Empregado Doméstico", "Salário + VT + encargos eSocial (estimativa).", "custo-empregado-domestico", "emd_gui.pyw"),
    ("🛣️", "Custo Total por km", "Combustível + fixos diluídos em R$/km.", "custo-total-por-km", "ckm_gui.pyw"),
    ("💼", "13º Proporcional", "13º salário proporcional CLT menos adiantamento.", "decimo-terceiro-proporcional", "d13_gui.pyw"),
    ("📬", "Estimativa de Frete", "Heurística de frete por peso, distância e modalidade.", "estimativa-frete", "fre_gui.pyw"),
    ("🏡", "Seguro Residencial", "Estima prêmio anual sobre imóvel + conteúdo.", "estimativa-seguro-residencial", "sgr_gui.pyw"),
    ("🏨", "Hospedagem × Aluguel", "Compara mês em hospedagem com aluguel + custos.", "hospedagem-vs-aluguel", "hos_gui.pyw"),
    ("🧠", "Planejador da Curva de Ebbinghaus & Revisões", "Cronograma de repetição espaçada (24h, 7d, 15d, 30d, 60d), modelo de retenção exponencial e gráfico comparativo", "planejador-ciclo-ebbinghaus", "ebb_gui.pyw"),
    ("🏥", "Reajuste Plano de Saúde", "Projeção composta da mensalidade ano a ano.", "reajuste-plano-saude", "rps_gui.pyw"),
    ("🍞", "Rendimento Pão Caseiro", "Quantos pães saem da fornada e custo unitário.", "rendimento-pao-caseiro", "pad_gui.pyw"),
    ("🧼", "Sabão Caseiro", "Rendimento, custo por uso e economia vs comercial.", "rendimento-sabao-caseiro", "sbo_gui.pyw"),
    ("🏋️", "Academia × Equipamentos", "Compara mensalidade com comprar aparelhos em casa.", "academia-vs-equipamentos", "acd_gui.pyw"),
    ("📝", "Analisador de Desempenho em Simulados e Provas", "Pontuação líquida Cebraspe e Múltipla Escolha, análise de risco de chute, ritmo de prova e nota de corte", "analisador-desempenho-simulados", "qsm_gui.pyw"),
    ("☕", "Café Casa × Cafeteria", "Custo mensal do café em casa vs cafeteria.", "cafe-casa-vs-cafeteria", "cfh_gui.pyw"),
    ("🔑", "Caução de Aluguel", "Depósito/caução e custo de oportunidade.", "calculadora-caucao", "cau_gui.pyw"),
    ("🎓", "Calculadora de ROI & Payback de Pós-Graduação", "Retorno sobre investimento de graduação e pós, tempo de payback salarial, fluxo de caixa e VPL", "calculadora-roi-educacao-pos", "cbf_gui.pyw"),
    ("🖨️", "Cartucho × Toner", "Custo por página e gasto mensal de impressão.", "cartucho-vs-toner", "tdc_gui.pyw"),
    ("💳", "Cashback Real", "Cashback líquido após anuidade, IOF e teto.", "cashback-real", "csh_gui.pyw"),
    ("💊", "Genérico × Marca", "Compara preço de marca vs genérico por comprimido.", "comparador-generico-marca", "gen_gui.pyw"),
    ("📶", "Planos de Internet", "Compara planos por R$/Mbps e fidelidade.", "comparador-planos-internet", "itn_gui.pyw"),
    ("📅", "Contas Fixas", "Soma mensal e alerta de vencimentos próximos.", "controle-contas-fixas", "cfx_gui.pyw"),
    ("🎒", "Custo Escola Particular", "Anuidade + material, uniforme, transporte e extras.", "custo-escola-particular", "ecp_gui.pyw"),
    ("🫧", "Diluição Água Sanitária", "ml de hipoclorito para ppm de desinfecção.", "diluicao-agua-sanitaria", "aws_gui.pyw"),
    ("🧴", "Diluição Limpeza", "Dilui concentrados (C1·V1=C2·V2).", "diluicao-limpeza", "dil_gui.pyw"),
    ("🍱", "Distribuição de Calorias e Macros por Refeição", "Divisão ótima de proteínas, gorduras e carboidratos em 3 a 6 refeições com limiar de leucina e timing", "distribuicao-refeicoes-macros", "drm_gui.pyw"),
    ("🌿", "Economia Horta Caseira", "Colheita vs mercado menos insumos e tempo.", "economia-horta-caseira", "hrt_gui.pyw"),
    ("🚗", "Entrada Carro Seminovo", "Financiamento Price + IPVA/seguro/docs.", "entrada-carro-seminovo", "sem_gui.pyw"),
    ("🏠", "Entrada Financiamento", "Entrada %, saldo e prestação Price do imóvel.", "entrada-financiamento", "ent_gui.pyw"),
    ("👕", "Lavanderia × Máquina", "Compara custo mensal lavanderia vs lavar em casa.", "lavanderia-vs-maquina", "lav_gui.pyw"),
    ("✈️", "Meta Poupança Viagem", "Quanto guardar por mês para a viagem.", "meta-poupanca-viagem", "rvg_gui.pyw"),
    ("🎉", "Orçamento de Festa", "Comida, bebida e fixos por convidados.", "orcamento-festa", "fan_gui.pyw"),
    ("📦", "Orçamento de Mudança", "Caminhões, caixas, ajudantes, km e seguro.", "orcamento-mudanca", "mdv_gui.pyw"),
    ("👨‍👩‍👧", "Pensão Alimentícia", "Estimativa por % da renda líquida e filhos.", "pensao-alimenticia", "pen_gui.pyw"),
    ("🐶", "Petsitter × Creche", "Compara petsitter, creche e hotelzinho.", "petsitter-vs-creche", "pts_gui.pyw"),
    ("🛒", "Compras no Atacado", "Quanto comprar sem estourar orçamento/validade.", "planejador-compras-atacado", "pat_gui.pyw"),
    ("⚖️", "Prestação × Aluguel", "Custo mensal comprar vs alugar com valorização.", "prestacao-vs-aluguel", "pai_gui.pyw"),
    ("💊", "Reembolso Plano de Saúde", "Estima reembolso por tabela, % e coparticipação.", "reembolso-plano-saude", "rms_gui.pyw"),
    ("🏖️", "Simulador de Abono Pecuniário — Venda de Férias CLT", "Venda de 1/3 de férias (10 dias), isenção de INSS e IRPF, adiantamento e saldo no retorno do trabalho", "simulador-abono-pecuniario-ferias", "abn_gui.pyw"),
    ("🎬", "Streaming × Cinema", "Assinaturas vs ingressos e pipoca no mês.", "streaming-vs-cinema", "cin_gui.pyw"),
    ("🤸", "Academia Infantil", "Mensalidade + uniforme + transporte e extras.", "academia-infantil", "aci_gui.pyw"),
    ("🍚", "Arroz & Feijão", "Rendimento cru→cozido e custo por porção.", "arroz-feijao-porcao", "arf_gui.pyw"),
    ("👶", "Custo Creche", "Mensalidade + material + alimentação.", "custo-creche", "crh_gui.pyw"),
    ("🗣️", "Curso de Idioma", "Custo total e por aula de curso de idioma.", "custo-curso-idioma", "idi_gui.pyw"),
    ("👓", "Custo de Óculos", "Armação + lentes + exame − desconto.", "custo-oculos", "ocl_gui.pyw"),
    ("🏷️", "Desconto Progressivo", "Faixas de desconto por valor de compra.", "desconto-progressivo", "dpg_gui.pyw"),
    ("🧴", "Diluição Alvejante", "ml de cloro para ppm na lavagem.", "diluicao-alvejante", "alv_gui.pyw"),
    ("🧺", "Diluição Amaciante", "Partes produto:água para o volume final.", "diluicao-amaciante", "amc_gui.pyw"),
    ("🅿️", "Estacionamento Mensalista", "Mensalista vs avulso (hora ou diária).", "estacionamento-mensalista", "ems_gui.pyw"),
    ("🍞", "Fermento Natural", "Escalas de alimentação do starter.", "fermento-natural", "fer_gui.pyw"),
    ("⛽", "Gasolina Postos", "Compara postos com custo do desvio.", "gasolina-postos", "gsp_gui.pyw"),
    ("🍽️", "Gorjeta Buffet", "Buffet × pessoas + couvert + gorjeta %.", "gorjeta-buffet", "buf_gui.pyw"),
    ("🐾", "Hospedagem Pet", "Hotelzinho/creche durante a viagem.", "hospedagem-pet", "hpv_gui.pyw"),
    ("🧥", "Lavagem a Seco × Casa", "Tinturaria vs lavar peças delicadas em casa.", "lavagem-a-seco", "lvs_gui.pyw"),
    ("🥬", "Lista da Feira", "Soma itens e alerta se estoura o orçamento.", "lista-feira-orcamento", "lfe_gui.pyw"),
    ("💅", "Manicure Salão × Casa", "Salão vs kit e esmaltes em casa.", "manicure-spa-vs-casa", "mnc_gui.pyw"),
    ("📚", "Material Escolar", "Soma lista e compara com kit da escola.", "material-escolar", "mte_gui.pyw"),
    ("📱", "Planos de Celular", "Compara planos por GB e excedente.", "plano-celular-gb", "clb_gui.pyw"),
    ("🎯", "Poupança & Meta", "Projeção com juros e meses até a meta.", "poupanca-meta", "pmt_gui.pyw"),
    ("🚙", "Seguro Auto × Franquia", "Custo esperado prêmio + franquia×sinistros.", "seguro-auto-franquia", "sfa_gui.pyw"),
    ("🏢", "Taxa Extra Condomínio", "Rateio igualitário ou por fração ideal.", "taxa-extra-condominio", "tcx_gui.pyw"),
    ("🧾", "Taxa da Maquininha", "Líquido após taxa débito/crédito/parcelado.", "taxa-maquininha", "maq_gui.pyw"),
    ("🚌", "Uber × Ônibus", "App vs transporte público no mês.", "uber-vs-onibus", "ubr_gui.pyw"),
    ("🧽", "Validade Limpeza", "PAO após abertura de produtos de limpeza.", "validade-produtos-limpeza", "vlm_gui.pyw"),
    ("🦉", "Analisador de Cronotipo e Rotina Circadiana", "Questionário científico de Horne & Östberg (MEQ), classificação Cotovia vs Coruja e mapa de janelas de foco, treino e sono", "analisador-cronotipo-sono-rotina", "cts_gui.pyw"),
    ("👔", "Calculadora de Custo de Funcionário CLT para Empresa", "Custo real da contratação CLT para MEI, Simples Nacional e Lucro Presumido: encargos, FGTS, provisões e benefícios", "calculadora-custo-contratacao-funcionario", "cdf_gui.pyw"),
    ("📑", "Calculadora de Rescisão Trabalhista CLT", "Cálculo completo de rescisão contratual: demissão sem justa causa, pedido, acordo mútuo, aviso proporcional, FGTS e férias", "calculadora-rescisao-trabalhista", "rst_gui.pyw"),
    ("🛡️", "Calculadora de Seguro-Desemprego", "Cálculo oficial pela Lei 13.134/2015, carência por solicitação (1ª, 2ª ou 3ª vez), faixas do MTE e parcelas", "calculadora-seguro-desemprego", "csd_gui.pyw"),
    ("🩺", "Controle de Pressão Arterial", "Classifica PAS/PAD (mmHg) pelas faixas AHA/ESC simplificadas; medição única ou média de N leituras; aviso educativo", "controle-pressao-arterial", "pas_gui.pyw"),
    ("🏡", "Custo Home Office vs Escritorio", "Compara extras do home office com o custo mensal de deslocamento ao escritorio, diferenca e break-even.", "custo-home-office", "hof_gui.pyw"),
    ("🌱", "Custo Jardineiro", "Jardineiro vs você mesmo (horas+insumos).", "custo-jardineiro", "jrd_gui.pyw"),
    ("🏋️", "Índice de Carga de Treino (sRPE)", "Carga session-RPE (RPE×min), soma semanal, média diária e classificação leve/moderada/alta/muito alta", "indice-carga-treino", "ict_gui.pyw"),
    ("🍿", "Cinema 2D × 3D", "Compara custo 2D vs 3D com pipoca.", "ingresso-cinema-3d", "icn_gui.pyw"),
    ("🎤", "Ingresso Show", "Ingresso + taxa + transporte + consumo.", "ingresso-show", "shw_gui.pyw"),
    ("🪵", "Madeira p/ Reforma", "Quantidade com perda, frete e mão de obra.", "madeira-reforma", "mad_gui.pyw"),
    ("💍", "Orçamento Lua de Mel", "Passagem, hotel, passeios, comida e seguro.", "orcamento-lua-de-mel", "ldm_gui.pyw"),
    ("📝", "Planejador de Revisão para Provas", "Cronograma diário de páginas/tópicos e horas de estudo até a prova, com alerta de carga impossível", "planejador-revisao-provas", "rvp_gui.pyw"),
    ("🎯", "Planejador de Sessão de Foco", "Monta blocos de deep work com pausas, agenda HH:MM e aproveitamento % do tempo disponível", "planejador-sessao-foco", "fcs_gui.pyw"),
    ("🎓", "Simulador do Novo FIES & Amortização", "Financiamento estudantil FIES, coparticipação no curso, retenção percentual em folha pelo eSocial e prazo de quitação", "simulador-financiamento-estudantil-fies", "fie_gui.pyw"),
    ("🎁", "Simulador de PLR", "Participação nos Lucros: bruto, IR e líquido por meta e múltiplo de salários.", "simulador-plr", "plr_gui.pyw"),
    ("💠", "Taxa Pix Recebimento", "Líquido após taxa % e fixa no Pix.", "taxa-pix-recebimento", "txp_gui.pyw"),
    ("🥗", "Calculadora de Densidade Calórica & Saciedade", "Índice de saciedade de Holt e volumetria: comparação de volume no prato para controle da fome no emagrecimento", "calculadora-densidade-calorica-saciedade", "dcs_gui.pyw"),
    ("🏙️", "Comparador Salário × Cidade", "Ajusta salários pelo índice de custo de vida entre duas cidades e compara poder de compra.", "comparador-salario-cidade", "scd_gui.pyw"),
    ("💪", "Índice de Massa Muscular (FFMI)", "Calcula FFMI e FFMI normalizado a partir de peso, altura e % de gordura, com classificação aproximada.", "indice-massa-muscular", "imm_gui.pyw"),
    ("📈", "Simulador de Dissídio & Convenção", "Reajuste salarial, retroativo desde a data-base e total com benefícios", "simulador-dissidio", "dsi_gui.pyw"),
    ("✈️", "Adaptação ao Jet Lag", "Diferença de fuso, preparação do sono antes de viajar e dias para o corpo se ajustar", "adaptacao-jet-lag", "jtl_gui.pyw"),
    ("🏋️", "Analisador de Volume de Treino Semanal (Hipertrofia)", "Calcula séries semanais efetivas e faixas adaptativas (MV, MEV, MAV, MRV de Mike Israetel / RP) com detector de junk volume", "analisador-volume-treino-semanal", "vth_gui.pyw"),
    ("🧠", "Calculadora de Densidade de Estudo & Foco Cognitivo", "Calcula a taxa de aproveitamento líquido em sessões de estudo (Pomodoro/Ultradiano), índice de dispersão e fadiga mental de Sweller", "calculadora-densidade-estudo-pomodoro", "epm_gui.pyw"),
    ("🧾", "Calculadora IR Simplificado", "IRPF mensal: base, aliquota efetiva, IR devido e liquido (tabela progressiva 2024/2025).", "calculadora-ir-simplificado", "irs_gui.pyw"),
    ("📚", "Carga Horária & Créditos", "Soma créditos e horas da grade semestral, equivalência crédito→hora configurável e alerta de limite", "carga-horaria-creditos", "chh_gui.pyw"),
    ("🔋", "Cargas do Power Bank", "Quantas recargas reais o power bank dá no celular e se pode levar no avião", "cargas-power-bank", "pwb_gui.pyw"),
    ("💱", "Cartão ou Espécie na Viagem", "Compara cartão de crédito, dinheiro vivo e conta global com spread, IOF e sobra", "cartao-ou-especie-viagem", "cxv_gui.pyw"),
    ("🎤", "Checklist de Preparacao para Entrevista", "Checklist ponderado: marque tarefas (curriculo, pesquisa, perguntas, rota, roupa, documentos), ajuste pesos e veja % de prontidao, criticos faltando e tempo restante", "checklist-entrevista-emprego", "cie_gui.pyw"),
    ("🏨", "Comparador de Hospedagens", "Hotel x pousada x Airbnb com limpeza, taxa do site, café e transporte por pessoa/noite", "comparador-hospedagens", "hsp_gui.pyw"),
    ("💼", "Comparador Salário × Benefícios", "Compara duas propostas de emprego: bruto, VR, VT, plano de saúde e outros — pacote mensal, diferença e equivalente em bruto.", "comparador-salario-beneficios", "csb_gui.pyw"),
    ("💊", "Agenda de Medicação por Horários", "Cronograma de doses por intervalo em horas; próxima dose a partir de agora; alerta de sobreposição entre remédios no mesmo horário (±30 min)", "controle-medicacao-horarios", "mdh_gui.pyw"),
    ("🏥", "Custo Consulta Especialista", "Compara consulta particular vs plano: coparticipacao, retornos, exames e break-even.", "custo-consulta-especialista", "ces_gui.pyw"),
    ("🌐", "Imposto de Compra Internacional", "Remessa Conforme: Imposto de Importação 20%/60% + ICMS por dentro e total em reais", "imposto-compra-internacional", "imx_gui.pyw"),
    ("😴", "Índice de Qualidade do Sono (PSQI simplificado)", "Questionário educativo inspirado no PSQI: escore 0–21, classificação e dicas de higiene do sono", "indice-qualidade-sono-psqi", "psq_gui.pyw"),
    ("🛡️", "Prazos do Consumidor", "Até quando desistir da compra, reclamar de defeito, usar a garantia e cobrar o conserto (CDC)", "prazos-direito-consumidor", "cdc_gui.pyw"),
    ("🎓", "ROI de Curso & Certificação Profissional", "Payback e ROI de bootcamps e certificações (AWS, PMP, Cisco) com custo de oportunidade das horas de estudo.", "roi-curso-certificacao", "roi_gui.pyw"),
    ("⏰", "Simulador de Banco de Horas & Compensação (CLT)", "Controle de saldo do banco de horas CLT (art. 59), prazos legais de prescrição (6 meses ou 1 ano) e liquidação com adicional e DSR", "simulador-banco-horas-compensacao", "bhc_gui.pyw"),
    ("🫀", "Analisador de Perfil Lipídico & Risco Aterogênico (SBC)", "Calcula índices aterogênicos (Castelli I e II, razão TG/HDL, Não-HDL) e estratificação de risco cardiovascular da Sociedade Brasileira de Cardiologia", "analisador-perfil-lipidico-cardiovascular", "apl_gui.pyw"),
    ("🍽️", "Calculadora VR/VA Mensal", "Credito mensal de Vale Refeicao e Vale Alimentacao com desconto em folha e media por dia trabalhado", "calculadora-beneficio-vr-va", "vva_gui.pyw"),
    ("🤝", "Contribuicao Sindical & Assistencial", "Simula desconto sindical/assistencial: mensal, anual, % efetivo e liquido", "calculadora-contribuicao-sindical", "isd_gui.pyw"),
    ("💼", "Calculadora de Custo de Estagiário para Empresas (Lei 11.788)", "Calcula o custo total real de contratação de estagiário (bolsa, auxílio-transporte integral, seguro de vida, provisão de recesso remunerado e taxa de agente integrador)", "calculadora-custo-estagiario-empresa", "cee_gui.pyw"),
    ("🔧", "Consertar ou Trocar o Celular", "Custo por ano de consertar x comprar novo, com venda do quebrado e regra dos 50%", "consertar-ou-trocar-celular", "cvn_gui.pyw"),
    ("💧", "Controle de Agua Diaria por Copos", "Meta diaria de agua em ml e copos por peso, atividade, clima quente e progresso do que ja bebeu", "controle-agua-diaria-copos", "agd_gui.pyw"),
    ("📸", "Espaço para Fotos e Vídeos", "Quantas fotos e minutos de vídeo cabem no espaço livre do celular e em quantos dias enche", "espaco-fotos-videos-celular", "arm_gui.pyw"),
    ("📦", "Frete Grátis Vale a Pena?", "Completar o carrinho até o mínimo do frete grátis ou pagar o frete: qual sai melhor", "frete-gratis-vale-a-pena", "fgr_gui.pyw"),
    ("😰", "Índice de Estresse Percebido (simplificado)", "Questionário educativo Likert 0–4: escore 0–20, classificação baixa/moderada/alta e dicas genéricas", "indice-estresse-percebido", "iep_gui.pyw"),
    ("📈", "Indice de Produtividade Pessoal", "Escore diario 0-100 com % foco, % conclusao de tarefas e classificacao a partir de horas e interrupcoes", "indice-produtividade-pessoal", "ipp_gui.pyw"),
    ("📡", "Internet Ideal para Casa", "Quantos Mbps a casa precisa pelo uso simultâneo no pico (streaming, videochamada, jogos)", "internet-ideal-casa", "mbp_gui.pyw"),
    ("🚦", "Multa de Trânsito e Pontos", "Valor da multa com desconto de 20%/40% (SNE), pontos e quanto falta para suspender a CNH", "multa-transito-pontos", "mtv_gui.pyw"),
    ("📊", "Matriz Eisenhower", "Organize tarefas nos 4 quadrantes (fazer agora, agendar, delegar, eliminar) com contagens e ordem sugerida", "organizador-tarefas-eisenhower", "eis_gui.pyw"),
    ("📅", "Planejador de Cronograma de Estudo para Editais & Provas", "Calcula a viabilidade temporal de fechamento do edital até o concurso, metas semanais de tópicos e divisão de carga horária por peso da matéria", "planejador-cronograma-estudo-edital", "pce_gui.pyw"),
    ("📖", "Planejador de Leituras Semanais", "Meta operacional da semana: paginas/dia, minutos/dia, se cabe no tempo e data estimada de termino", "planejador-leituras-semanais", "pls_gui.pyw"),
    ("⚡", "Sessão Flash de Revisão", "Monta blocos de estudo para os minutos disponíveis agora, prioriza tópicos fracos (notas 1-5) e alerta se o tempo não cobre tudo", "planejador-revisao-flash-rapida", "frp_gui.pyw"),
    ("☁️", "Plano de Nuvem para Backup", "Em quantos meses cada plano de nuvem enche com suas fotos e vídeos e qual o mais barato que aguenta", "plano-nuvem-backup", "nuv_gui.pyw"),
    ("☣️", "Adicional de Insalubridade CLT", "10/20/40% sobre salário mínimo ou base configurável; impacto mensal e anual", "calculadora-adicional-insalubridade", "ins_gui.pyw"),
    ("🥬", "Calendário da Horta", "Data de colheita de cada hortaliça e plantio escalonado para colher sem parar", "calendario-da-horta", "cpl_gui.pyw"),
    ("🧳", "Checklist de Onboarding no Novo Emprego", "Checklist ponderado: RH, sistemas, apresentação ao time, mentor e equipamentos — % de prontidão, críticos faltando e dias sugeridos restantes", "checklist-onboarding-emprego", "cob_gui.pyw"),
    ("🚪", "Checklist de Saida do Emprego", "Checklist ponderado de desligamento: devolucao de notebook e equipamentos, revogacao de acessos, carta e aviso previo, FGTS/TRCT e documentos, handover e networking — % pronto e criticos faltando", "checklist-saida-emprego", "cse_gui.pyw"),
    ("🎓", "Comparador de Propostas de Estagio", "Compara duas propostas de estagio: bolsa, VT, VR, horas por semana e deslocamento — pacote mensal, R$/hora efetiva e melhor oferta.", "comparador-proposta-estagio", "cpe_gui.pyw"),
    ("☕", "Controle de Doses de Cafeína no Dia", "Soma doses diárias em mg (café, chá, energético), limite configurável e alerta ao estourar", "controle-cafeina-doses-dia", "cfd_gui.pyw"),
    ("🪑", "Timer de Pausa Postural", "Cronograma de levantadas ao longo do dia, total de pausas e comparativo estimado sentado versus em pe, com timer opcional", "controle-postura-timer", "ptr_gui.pyw"),
    ("🗓️", "Cronograma do Evento", "Datas de cada tarefa de festa, viagem ou mudança contando de trás pra frente, com atrasadas", "cronograma-do-evento", "cre_gui.pyw"),
    ("🧊", "Descongelar com Segurança", "Tempo para descongelar carne, frango ou peixe e a hora certa de tirar do freezer", "descongelar-com-seguranca", "dsc_gui.pyw"),
    ("🚪", "Hora de Sair", "Que horas pôr o alarme, se arrumar e sair de casa para chegar no horário", "hora-de-sair", "hsa_gui.pyw"),
    ("😊", "Índice de Satisfação no Trabalho", "Questionário educativo Likert 0–4 em cinco dimensões (salário, chefia, colegas, crescimento, equilíbrio): média, classificação e dimensão mais fraca", "indice-satisfacao-trabalho", "ist_gui.pyw"),
    ("🥄", "Medidas de Cozinha", "Converte xícara, colher e copo em gramas e ml (e o contrário) por ingrediente", "medidas-de-cozinha", "mcl_gui.pyw"),
    ("🗣️", "Meta de Vocabulario por Semana", "Palavras por dia, minutos necessarios, se a meta cabe no tempo e ritmo atual vs necessario", "meta-vocabulario-idioma", "mvi_gui.pyw"),
    ("🍽️", "Planejador de Intervalo de Almoco", "Calcula horario de volta, minutos efetivos para comer e alerta quando o almoco fica apertado", "planejador-intervalo-almoco", "pia_gui.pyw"),
    ("✍️", "Planejador de Meta de Redacao", "Calcula o que falta escrever, minutos necessarios, se cabe na sessao de hoje e ritmo sugerido para ENEM, escola ou blog", "planejador-meta-redacao", "pmr_gui.pyw"),
    ("⏱️", "Simulador Hora Extra 50% e 100%", "CLT tipica: valor da HE50, HE100, total de extras e salario + extras pelo divisor mensal.", "simulador-hora-extra-50-100", "hex_gui.pyw"),
    ("🪴", "Terra para Vasos", "Litros de substrato e drenagem por vaso, mistura terra/húmus/areia e quantos sacos comprar", "terra-para-vasos", "sbv_gui.pyw"),
    ("⚠️", "Adicional de Periculosidade CLT", "30% típico sobre salário-base; proporcionalidade da jornada; mensal e anual", "calculadora-adicional-periculosidade", "per_gui.pyw"),
    ("📅", "DSR sobre Horas Extras", "Reflexo do descanso semanal sobre o total de HE do mes (proporcao domingos+feriados/dias uteis)", "calculadora-dsr-hora-extra", "dsr_gui.pyw"),
    ("📋", "Checklist 1a Semana de Estagio", "Checklist ponderado da primeira semana: termo, cracha, mentor, acessos e tarefas — marque itens e veja % pronto e criticos faltando", "checklist-primeira-semana-estagio", "cps_gui.pyw"),
    ("🥤", "Controle de Hidratação no Escritório", "Meta de água no expediente, volume restante e horário sugerido do próximo copo conforme o ritmo alvo", "controle-hidratacao-escritorio", "hid_gui.pyw"),
    ("🔥", "Indice simplificado de burnout", "Questionario educativo de 5 itens Likert (exaustao, cinismo, eficacia, sono, desconexao) com escore, nivel e dicas; aviso CVV 188", "indice-burnout-simplificado", "ibs_gui.pyw"),
    ("👁️", "Planejador Regra 20-20-20", "Cronograma de pausas oculares: a cada 20 min de tela, olhar 20 pes (~6 m) por 20 segundos", "planejador-pausa-olhos-20-20-20", "p20_gui.pyw"),
    ("💧", "Água Mineral × Filtro", "Compara galão/mês com o custo diluído do purificador e payback.", "agua-mineral-vs-filtro", "agm_gui.pyw"),
    ("🎓", "Analisador de Nota de Corte & Média Ponderada SiSU/ENEM", "Calcula a média ponderada do ENEM com os pesos específicos da universidade, bônus regional, saldo de pontos em relação à nota de corte e disciplina de maior impacto", "analisador-nota-corte-sisu-enem", "nce_gui.pyw"),
    ("📖", "Analisador de Ritmo de Leitura & Compreensão (PPM)", "Calcula velocidade de leitura em PPM, PPM efetivo ponderado pela taxa de retenção e projeção de horas para concluir livros e editais", "analisador-ritmo-leitura-compreensao", "rtc_gui.pyw"),
    ("🗃️", "Caixa de Leitner (Intervalos)", "Leitner classico: N caixas, intervalos em dias configuraveis, promover/rebaixar na revisao e agenda de carga diaria nos proximos D dias", "caixa-leitner-intervalos", "ivl_gui.pyw"),
    ("🌙", "Calculadora Adicional Noturno", "CLT art. 73: adicional minimo de 20% na hora noturna (22h-5h), com jornada reduzida 52min30s opcional.", "calculadora-adicional-noturno", "adt_gui.pyw"),
    ("📞", "Calculadora de Adicional de Sobreaviso & Prontidão (CLT)", "Calcula a remuneração de sobreaviso (1/3), prontidão (2/3), acionamentos em hora extra e reflexos trabalhistas em DSR, férias e 13º", "calculadora-adicional-sobreaviso-prontidao", "sbp_gui.pyw"),
    ("🌙", "Calculadora de Ciclos de Sono & Despertar sem Inércia", "Calcula horários ótimos para dormir e acordar baseados em ciclos de 90 minutos de sono REM para evitar cansaço ao despertar", "calculadora-ciclos-sono-rem", "csr_gui.pyw"),
    ("👶", "Calculadora de Dosagem Pediátrica por Peso Corporal", "Calcula doses precisas em gotas, mL e mg para paracetamol, dipirona, ibuprofeno e amoxicilina com base no peso e alertas de segurança", "calculadora-dosagem-medicamento-pediatrico", "dmp_gui.pyw"),
    ("💊", "Calculadora de Dosagem de Suplementação Esportiva (ISSN)", "Calcula dosagens científicas individualizadas de creatina (manutenção vs saturação), whey protein por déficit proteico, beta-alanina e cafeína pré-treino", "calculadora-dosagem-suplementacao-esportiva", "dsw_gui.pyw"),
    ("⚖️", "Calculadora de Equiparação Salarial & Reflexos Trabalhistas (Art. 461 CLT)", "Calcula diferenças salariais de desvio de função com reflexos em 13º, férias com 1/3, FGTS com 40%, horas extras, DSR e prescrição quinquenal", "calculadora-equiparacao-salarial-clt", "eqs_gui.pyw"),
    ("🔥", "Calculadora de Taxa Metabólica & TDEE (Katch-McArdle)", "Calcula a TMB baseada em Massa Livre de Gordura (LBM), Gasto Energético Total Diário (TDEE) e cotas calóricas para cutting e bulking limpo", "calculadora-taxa-metabolica-katch-mcardle", "kmc_gui.pyw"),
    ("🔋", "Calculadora de Tempo de Recuperação Muscular & Supercompensação", "Calcula horas de descanso necessárias por grupamento muscular e exercício, identificando a janela ótima de supercompensação (Selye/GAS)", "calculadora-tempo-recuperacao-muscular", "trm_gui.pyw"),
    ("❤️", "Calculadora de Zonas de Frequência Cardíaca (Karvonen & HRR)", "Calcula as 5 zonas de treinamento individualizadas pela FC de Reserva (Karvonen), comparativo com Tanaka/Fox e gasto calórico em cada zona", "calculadora-zonas-frequencia-cardiaca-karvonen", "kvn_gui.pyw"),
    ("📉", "Carga Semanal e Risco de Burnout", "Índice 0–100 de carga semanal: horas nos 7 dias, extras, noites com sono < 6 h e fins de semana trabalhados — pesos documentados e faixa baixo/atenção/alto", "carga-semanal-risco-burnout", "rsg_gui.pyw"),
    ("🏅", "Checklist Prova de Certificação", "Checklist ponderado para certificação: edital, simulados N/meta, lab, inscrição, data, revisão e descanso — % prontidão, críticos e ratio de simulados", "checklist-prova-certificacao", "crt_gui.pyw"),
    ("🎤", "Checklist Prova Oral / Banca", "Checklist ponderado para defesa oral: documento, slides, ensaio cronometrado, perguntas antecipadas, hidratacao, traje, backup PDF e chegada — % prontidao, criticos e tempo restante", "checklist-prova-oral-banca", "brk_gui.pyw"),
    ("🦷", "Plano Odontológico × Particular", "Compara mensalidade + coparticipação do plano odonto com ir particular.", "comparador-plano-odonto", "odt_gui.pyw"),
    ("💳", "Consignado × Crédito Pessoal", "Compara prestação Price, juros totais e CET aproximado dos dois créditos.", "consignado-vs-credito-pessoal", "ccn_gui.pyw"),
    ("🚌", "Custo de Deslocamento ao Trabalho", "Custo mensal do commute: R$/km no carro ou passagem, horas no transito e total economico com valor da sua hora.", "custo-deslocamento-trabalho", "cmt_gui.pyw"),
    ("🧷", "Custo Fralda Geriátrica", "Estima pacotes/mês, extras (creme/lenço) e gasto anual.", "custo-fralda-geriatrica", "frg_gui.pyw"),
    ("🛣️", "Pedágio × TAG", "Compara pedágio avulso com desconto e mensalidade da TAG.", "custo-pedagio-tag", "tag_gui.pyw"),
    ("🎨", "Custo Pintura de Parede", "Estima tinta (demãos e perda), primer opcional e mão de obra por m².", "custo-pintura-parede", "pnt_gui.pyw"),
    ("🏋️", "Estimativa 1RM (Epley/Brzycki)", "Peso x reps para 1RM (Epley e Brzycki), tabela %1RM para prescrição e carga sugerida para N repetições", "estimativa-1rm-epley", "epl_gui.pyw"),
    ("🩸", "Estimativa HbA1c & eAG", "Converte HbA1c (%) e glicemia média estimada (eAG) pela fórmula Nathan, com mg/dL e mmol/L e faixa ADA educativa.", "estimativa-hba1c-glicemias", "hba_gui.pyw"),
    ("🏃", "Estimativa VO2máx Cooper", "Teste Cooper 12 min e Rockport (1 milha) com VO2max estimado e classificação por idade/sexo.", "estimativa-vo2max-cooper", "vo2_gui.pyw"),
    ("📦", "Frete Sedex × PAC", "Compara preço, prazo e custo por dia antecipado entre Sedex e PAC.", "frete-sedex-vs-pac", "sdx_gui.pyw"),
    ("🔥", "Gás Encanado × Botijão", "Compara o custo mensal do botijão (GLP) com o gás natural encanado.", "gas-encanado-vs-botijao", "gne_gui.pyw"),
    ("⚖️", "Índice Equilíbrio Vida-Trabalho", "Índice 0–100 com pesos documentados: jornada semanal, lazer, sono, fins de semana livres, trabalho após 20h e satisfação — nível e dica personalizada", "indice-equilibrio-vida-trabalho", "wlb_gui.pyw"),
    ("😩", "Índice de Fadiga de Turno", "Escore 0–100 de fadiga em plantão: horas trabalhadas, sono, plantões seguidos, pausas e esforço RPE 1–10, com pesos documentados, nível e dica", "indice-fadiga-turno", "fad_gui.pyw"),
    ("🌿", "Indice Qualidade de Vida Semanal", "Seis dimensoes Likert 0-4 (fisica, sono, humor, relacoes, lazer, proposito) com indice 0-100, nivel, pior dimensao e dica semanal", "indice-qualidade-vida-semanal", "qol_gui.pyw"),
    ("🏦", "Lance de Consórcio", "Estima se vale dar lance para contemplação ou esperar o sorteio.", "lance-consorcio", "csc_gui.pyw"),
    ("🗺️", "Mapa de Gap de Habilidades", "Ranking de skills com gap entre nivel atual e alvo, prioridade ponderada e horas estimadas de desenvolvimento", "mapa-gap-habilidades", "skl_gui.pyw"),
    ("🩸", "Média de Glicemia Capilar", "Estatísticas de N medições em mg/dL (jejum e/ou pós-refeição): média, min, max, desvio, % acima de limiares editáveis e classificação educativa.", "media-glicemia-capilar", "glc_gui.pyw"),
    ("🎓", "Mensalidade Escola × Bolsa", "Mostra a economia anual com bolsa percentual + material e matrícula.", "mensalidade-escola-vs-bolsa", "bls_gui.pyw"),
    ("📖", "Meta de Páginas por Dia", "Prazo do livro, ritmo pág/h e min/dia: páginas necessárias por dia, viabilidade e data estimada de conclusão", "meta-paginas-leitura-dia", "pag_gui.pyw"),
    ("🃏", "Meta de Revisões Anki", "Estima revisões/dia no Anki (novos, intervalo ou retenção, tamanho do baralho) e diz se cabe no tempo disponível, com sugestão de novos/dia", "meta-revisoes-anki-diarias", "ank_gui.pyw"),
    ("🏋️", "Multa Cancelamento Academia", "Compara a multa de cancelamento com o custo de cumprir o contrato restante.", "multa-cancelamento-academia", "mca_gui.pyw"),
    ("🏢", "Orçamento Manutenção Predial", "Recorrentes + provisão de pintura/impermeabilização rateados por unidade.", "orcamento-manutencao-predial", "mpd_gui.pyw"),
    ("💍", "Orçamento Presentes de Casamento", "Estima gasto dos convidados e cobertura líquida da lista do casal.", "orcamento-presentes-casamento", "csg_gui.pyw"),
    ("🍽️", "Orçamento Reforma de Cozinha", "Soma móveis, eletros, bancada, revestimento, mão de obra e reserva %.", "orcamento-reforma-cozinha", "rcz_gui.pyw"),
    ("🧊", "Recuperação Pós-Treino", "Horas até treino duro, checklist sono/proteína/hidratação/mobilidade e score de prontidão pós-sessão", "planejador-recuperacao-pos-treino", "rmp_gui.pyw"),
    ("😴", "Planejador de Soneca Poder", "Power nap: duracao 10-20/30/90 min, horarios, inercia do sono e cafeina residual", "planejador-soneca-poder", "nap_gui.pyw"),
    ("⏱️", "Planejador de Gestão de Tempo e Estratégia de Prova", "Calcula tempo líquido por questão, reserva tática para redação e gabarito, checkpoints no relógio da sala e estratégia de passadas", "planejador-tempo-estrategia-prova", "etp_gui.pyw"),
    ("🧠", "Deep Work Semanal", "Meta semanal de horas deep work, registro Seg-Dom, total, % da meta, melhor dia, deficit/superavit e redistribuicao sugerida", "rastreador-deep-work-semanal", "dee_gui.pyw"),
    ("🗣️", "Ritmo de Fala da Apresentação", "Roteiro ou contagem de palavras + minutos do slot: WPM necessário, faixas lento/ideal/rápido, tempo no ritmo alvo, margem e sugestão de cortar ou expandir", "ritmo-fala-apresentacao", "spm_gui.pyw"),
    ("⭐", "Roteiro Entrevista STAR", "Monta resposta STAR (Situacao, Tarefa, Acao, Resultado), estima tempo de fala por WPM, checklist de qualidade do rascunho e pontuacao 0-100", "roteiro-entrevista-star", "beh_gui.pyw"),
    ("🧘", "Rotina Mobilidade Lombar", "Sessão de alongamento lombar: minutos, nível e intensidade geram sequência com tempos e checklist", "rotina-mobilidade-lombar", "mbl_gui.pyw"),
    ("🎂", "Saque-Aniversário FGTS", "Calcula o valor liberado no saque-aniversário pela tabela de faixas do FGTS.", "saque-aniversario-fgts", "fgs_gui.pyw"),
    ("✈️", "Seguro Viagem × Cobertura", "Compara dois planos de seguro viagem por custo/dia e cobertura médica por real.", "seguro-viagem-cobertura", "svj_gui.pyw"),
    ("💬", "Simulador de Negociação Salarial", "Pedido e mínimo aceitável (% ou R$), contraoferta e benefícios atuais vs novos; pacote bruto ou líquido simplificado, ganho anual e zona de acordo.", "simulador-negociacao-salarial", "neg_gui.pyw"),
    ("🚀", "Simulador de Transição de Carreira & Runway Financeiro", "Calcula o fôlego financeiro em meses (runway), burn rate mensal líquido e impacto de cortes de gastos para mudanças profissionais seguras", "simulador-transicao-carreira-reserva", "tcr_gui.pyw"),
    ("⏱️", "Tempo Liquido de Estudo", "Converte minutos brutos na mesa em tempo liquido real, com perdas por interrupcoes e distracao, eficiencia % e meta inversa de bruto para X liquido", "tempo-liquido-estudo", "tnr_gui.pyw"),
    ("🛞", "Troca de Pneu do Carro", "Vida útil em km, meses restantes, status e custo do jogo de pneus.", "troca-pneu-carro", "pne_gui.pyw"),
    ("🎤", "Notas de Voz", "Grava, transcreve no PC (sem internet) e separa lembrete e assunto. 🔥 Tendência do dia.", "notas-de-voz", "nvz_gui.pyw"),
    ("🎵", "Tocando Agora", "Widget do que está tocando e papel de parede com o tile — offline, sem API.", "tocando-agora", "npw_gui.pyw"),
    ("🖼️", "Visor de Fotos & Duplicadas", "Abre pastas de fotos na hora (cache de miniaturas), acha duplicadas e rostos, otimiza imagens. 🔥 Tendência do dia.", "visor-fotos", "vft_gui.pyw"),
    ("📝", "Atas de Reunião & Decisões", "Anotações de reuniões com extração de resumo executivo, decisões e tarefas com responsáveis e prazos — offline e privado. 🔥 Tendência do dia.", "atas-reuniao", "atr_gui.pyw"),
    ("🤖", "Canvas de Agentes de IA", "Canvas 2D interativo e planejador de fluxo de agentes de IA com herança de contexto e compilação de prompts. 🔥 Tendência do dia.", "canvas-agentes", "cag_gui.pyw"),
    ("💰", "Regra 50/30/20", "Planejamento financeiro rápido: 50% necessidades, 30% desejos e 20% poupança. 🔥 Tendência do dia.", "regra-50-30-20", "r50_gui.pyw"),
    ("🏦", "Conversor de Extrato CSV para OFX", "Converte extratos bancários CSV de bancos brasileiros (Nubank, Inter, Itaú, BB) para OFX padronizado. 🔥 Tendência do dia.", "conversor-extrato-csv-ofx", "cxo_gui.pyw"),
    ("🔤", "Escrita Sem Espaço (NoSpace)", "Escrita contínua sem barra de espaço com segmentação probabilística em tempo real. 🔥 Tendência do dia.", "escrita-sem-espaco", "nsp_gui.pyw"),
    ("📌", "Notas Adesivas & Dock (Stick-itt)", "Post-its flutuantes na tela com Always-on-Top, Fold em 1 linha e detecção de lembretes @horário. 🔥 Tendência do dia.", "notas-adesivas-dock", "stk_gui.pyw"),
    ("👁️", "Protetor Ocular & Filtro de Tela", "Pausas visuais 20-20-20 com detecção de ociosidade, exercícios oculares, filtro de luz azul e dimmer extra. 🔥 Tendência do dia.", "protetor-ocular", "eyg_gui.pyw"),
    ("🚀", "Super-Resolução & 120 FPS (Veyra)", "Upscaling Lanczos + Nitidez Adaptativa CAS, redução de ruído, cortina Antes/Depois e interpolação de vídeo 60/120 FPS. 🔥 Tendência do dia.", "estudio-upscale-video", "vnr_gui.pyw"),
    ("🗑️", "Desinstalador de Programas", "Desinstala apps e limpa sobras no disco e registro (substitui Revo Uninstaller)", "desinstalador", "uns_gui.pyw"),
    ("🎬", "Player de Vídeo", "Toca qualquer formato, legendas .SRT, velocidade e playlist (substitui VLC)", "player-video", "vpl_gui.pyw"),
    ("📝", "Editor de Texto", "Abas múltiplas, realce de sintaxe, regex e codificação UTF-8/ANSI (substitui Notepad++)", "editor-texto", "npp_gui.pyw"),
    ("⚡", "Copiador Rápido", "Cópia e movimentação veloz de arquivos e pastas com fila, pausa/retomada e verificação de hash (substitui TeraCopy)", "copiador-rapido", "cpr_gui.pyw"),
    ("🎭", "Estúdio de Cena", "Deck de clipe com camadas no quadro, falas ramificadas e troca ao vivo entre 7 idiomas. 🔥 Tendência do dia.", "estudio-cena", "ecn_gui.pyw"),
    ("🎮", "Motor V.E.T.O.R de Diálogos", "Motor de cenas em Canvas 2D, linha do tempo sincronizada e diálogo dinâmico em 7 idiomas (V.E.T.O.R). 🔥 Tendência do dia.", "motor-dialogos", "vtr_gui.pyw"),
    ("💼", "Copilot de Candidaturas & Vagas", "Mapeamento semântico de perguntas e selects de vagas (Gupy, Greenhouse, Lever) com banco de respostas e autofill. 🔥 Tendência do dia.", "copilot-candidaturas", "g3a_gui.pyw"),
    ("🧰", "Canivete do Técnico de PC", "Canivete portátil para técnicos de PC e manutenção Windows: backup/restauração de perfil, diagnóstico de saúde, reparos rápidos de rede/SFC e ordens de serviço. 🔥 Tendência do dia.", "canivete-tecnico-pc", "sak_gui.pyw"),
]

# Ferramentas que aceitam --pasta/--arquivo vindos dos botões da Hoje (as outras abrem normal)
FERRAMENTAS_COM_ARGS = {"faxina-disco", "organizador-downloads", "print-anotador"}  # Cursor F11

QSS = """
QWidget { background:#0e1016; color:#e7e9f0; font:10pt 'Segoe UI'; }
#title { font:800 22pt 'Segoe UI'; }
#sub { color:#8a93a8; }
QLineEdit { background:#161a23; border:1px solid #2d3550; border-radius:12px; padding:10px 14px; font:12pt 'Segoe UI'; }
QLineEdit:focus { border:1px solid #7c5cff; }
QScrollArea { border:0; }
#card { background:#243044; border:1px solid #5a6788; border-radius:16px; }
#card:hover { border:1px solid #7c5cff; background:#2c3750; }
#emoji { font:22pt 'Segoe UI Emoji'; }
#name { font:700 11pt 'Segoe UI'; color:#f2f4fa; }
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
#side { background:#161a23; border:1px solid #232a3b; border-radius:14px; padding:6px; font:10pt 'Segoe UI'; outline:none; }
#side::item { padding:9px 12px; border-radius:9px; color:#c7cbd8; margin:1px 0; }
#side::item:hover { background:#1a1f2b; color:#e7e9f0; }
#side::item:selected { background:rgba(124, 92, 255, 0.28); color:#f2f4fa; border:1px solid #7c5cff; font-weight:600; }
#side::item:selected:hover { background:rgba(124, 92, 255, 0.36); color:#ffffff; }
#badge { border-radius:12px; font:20pt 'Segoe UI Emoji'; }
#catlbl { font:8pt 'Segoe UI'; }
#hero { color:#6ee7b7; font:600 10pt 'Segoe UI'; }
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


# ---- Categorias (classificação automática por palavra-chave) ----
# Ordem IMPORTA: a primeira categoria cujo padrão casar vence. Ferramentas novas
# adicionadas por qualquer agente caem na categoria certa sozinhas.
CATEGORIAS = [
    ("💰 Finanças & Trabalho", ("financ", "finanç", "gasto", "orcament", "orçament", "pix",
        "boleto", "moeda", "clt", "salario", "salário", "juros", "imposto", "nf-e", "nfe", "ofx",
        "consorcio", "consórcio", "black-scholes", "opcoes", "opções", "curriculo", "currículo",
        "preco", "preço", "aposentadoria", "gorjeta", "extrato", "credito", "crédito", "mora",
        "banda", "resistor")),
    ("🏠 Casa, Pet & Pessoal", ("receita", "cozinha", "cafe", "café", "cerveja", "festa",
        "mudanca", "mudança", "pet", "racao", "ração", "cabelo", "aquario", "aquário", "hidropon",
        "horta", "jardim", "saude", "saúde", "imc", "gestacional", "gravidez", "habito", "hábito",
        "carro", "contato", "calendario", "calendário", "tarefa", "diario", "diário", "tamanho",
        "croche", "crochê", "trico", "tricô", "bike", "bicicleta", "marcha", "agenda", "ebook",
        "e-book", "receitas")),
    ("🔬 Ciência & Engenharia", ("fisica", "física", "quim", "quím", "dna", "bioinform",
        "estatist", "estatíst", "matriz", "combinat", "optica", "óptica", "circuito", "engrenagem",
        "hidraulic", "hidráulic", "concreto", "trelica", "treliça", "flambagem", "dilatac",
        "dilatação", "controle pid", "primo", "grafo", "huffman", "bayes", "benford", "quaternion",
        "monte carlo", "euler", "fourier", "gravitacional", "automato", "autômato", "matemat",
        "eletric", "elétric", "transformador", "snell", "engenharia", "nautic", "náutic",
        "navegac", "navegaç", "coorden", "viga", "rigidez", "circuitos", "optico", "óptico",
        "planetario", "planetário", "efemérides", "fisico")),
    ("🌐 Rede & Segurança", ("rede", "ip ", "dns", "wi-fi", "wifi", "ssl", "ssh", "firewall",
        "porta", "pcap", "siem", "seo", "cabecalho", "cabeçalho", "webhook", "hacker", "cifra",
        "feistel", "crc", "2fa", "cripto", "jwt", "sub-rede", "subrede", "geo ip", "scanner de rede",
        "nmap", "traceroute", "certificado", "vpn", "proxy", "morse", "pacote", "ads", "firewall")),
    ("💻 Dev & Dados", ("json", "sql", "sqlite", "xml", "cron", "uuid", " api", "python",
        "dados falsos", "grafico", "gráfico", "planilha", "schema", "diagrama", "sitemap", "bloom",
        "pareto", "regex", "markdown", "base", "hexa", "identificador", "snippet", "git", "docker",
        "huff", "spline")),
    ("🖼️ Imagem & Design", ("imagem", "foto", " cor", "cores", "paleta", "icone", "ícone", "svg",
        "gif", "sprite", "qr", "barras", "fonte", "tipografia", "webcam", "galeria", "desenho",
        "quadro", "print", "scanner de doc", "etiqueta", "pdf", "contraste")),
    ("🎵 Áudio & Vídeo", ("audio", "áudio", " som", "musica", "música", " voz", "mp3", "video",
        "vídeo", " tela", "metronomo", "metrônomo", "afinador", "midi", " onda", "legenda",
        "gravador")),
    ("✍️ Texto & Estudo", ("texto", " nota", "notas", "ocr", "fonetic", "fonétic", "legibilidade",
        "flashcard", "digitac", "digitação", "unicode", "leitura", "tradut", "idioma", "resumo")),
    ("🎮 Jogos & Diversão", ("sudoku", "quiz", "sorteio", "xadrez", "rpg", "dado", "gps falso",
        "cronometro", "cronômetro", " jogo", "roleta", "geografia", "palavra", "forca")),
    ("🗂️ Arquivos & Sistema", ("arquivo", "pasta", "disco", "zip", "compact", "backup", "windows",
        "processo", "servico", "serviço", "registro", "inicializ", "variavel", "variáve", "janela",
        "hosts", "duplicat", "renome", "metadado", "ntfs", "link", "boot", "atalho", "clipboard",
        "transferencia", "transferência", "sistema", "cpu", "memoria", "memória", "benchmark",
        "monitor", "tempo", "faxina", "busca", "recupera", "espaco", "espaço")),
]
CAT_OUTRAS = "🧰 Outras"
# 🔥 Tendências: ferramentas nascidas da Tendência do dia (lista em tendencias_caixa.json)
CAT_TENDENCIAS = "🔥 Tendências"
def _ler_tendencias():
    try:
        import json as _j
        for d in (HERE, getattr(sys, "_MEIPASS", HERE)):
            p = os.path.join(d, "tendencias_caixa.json")
            if os.path.isfile(p):
                with open(p, encoding="utf-8") as f:
                    return set(_j.load(f).get("pastas", []))
    except Exception:
        pass
    return set()
TENDENCIAS_PASTAS = _ler_tendencias()
CAT_CORES = {
    "💰 Finanças & Trabalho": "#ffd166", "🏠 Casa, Pet & Pessoal": "#6ee7b7",
    "🔬 Ciência & Engenharia": "#60a5fa", "🌐 Rede & Segurança": "#f87171",
    "💻 Dev & Dados": "#7c5cff", "🖼️ Imagem & Design": "#f472b6", "🎵 Áudio & Vídeo": "#fb923c",
    "✍️ Texto & Estudo": "#a3e635", "🎮 Jogos & Diversão": "#facc15",
    "🗂️ Arquivos & Sistema": "#94a3b8", CAT_OUTRAS: "#8a93a8",
    CAT_TENDENCIAS: "#ff6b35",
}
if _caixa_arquivo is not None:
    CAT_CORES[_caixa_arquivo.CAT_ARQUIVO] = _caixa_arquivo.COR_ARQUIVO
CARD_W, CARD_H, GAP = 272, 116, 12
F_NOME = QFont("Segoe UI", 11, 700)
F_DESC = QFont("Segoe UI", 9)


def elide_linhas(texto, fonte, largura, n):
    """Quebra o texto em até n linhas que cabem na largura, com reticências no fim."""
    fm = QFontMetrics(fonte)
    palavras = (texto or "").split()
    linhas, atual = [], ""
    for i, w in enumerate(palavras):
        tent = (atual + " " + w).strip()
        if fm.horizontalAdvance(tent) <= largura:
            atual = tent
            continue
        if atual:
            linhas.append(atual)
        atual = w
        if len(linhas) == n - 1:
            resto = " ".join([atual] + palavras[i + 1:])
            linhas.append(fm.elidedText(resto, Qt.TextElideMode.ElideRight, largura))
            return "\n".join(linhas)
    if atual:
        linhas.append(fm.elidedText(atual, Qt.TextElideMode.ElideRight, largura))
    return "\n".join(linhas[:n])
CAT_ORDEM = [CAT_TENDENCIAS] + [c[0] for c in CATEGORIAS] + [CAT_OUTRAS]
if _caixa_arquivo is not None:
    CAT_ORDEM.append(_caixa_arquivo.CAT_ARQUIVO)


def categoria_de(tool):
    """Classifica uma ferramenta (emoji, nome, desc, pasta, script) numa categoria.

    Duas passadas: primeiro só o NOME + pasta (sinal forte, evita ruído da descrição);
    se nada casar, inclui a descrição. Arquivadas vão para 📦 Arquivo.
    """
    nome = tool[1].lower()
    pasta = tool[3].lower()
    cat = CAT_TENDENCIAS if tool[3] in TENDENCIAS_PASTAS else None
    for nome_cat, kws in ([] if cat else CATEGORIAS):
        if any(k in nome or k in pasta for k in kws):
            cat = nome_cat
            break
    if cat is None:
        txt = nome + " " + tool[2].lower() + " " + pasta
        for nome_cat, kws in CATEGORIAS:
            if any(k in txt for k in kws):
                cat = nome_cat
                break
    if cat is None:
        cat = CAT_OUTRAS
    if _caixa_arquivo is not None:
        return _caixa_arquivo.categoria_efetiva(tool[3], cat)
    return cat


class Card(QFrame):
    def __init__(self, tool, caixa, fav):
        super().__init__(objectName="card")
        emoji, name, desc, folder, script = tool
        self.tool = tool
        self.key = folder
        self.caixa = caixa
        self.path = os.path.join(BASE, folder, script)
        self.exists = True if FROZEN else os.path.exists(self.path)
        cw, ch, _gap = caixa._medidas_grade() if hasattr(caixa, "_medidas_grade") else (CARD_W, CARD_H, GAP)
        self.setFixedSize(cw, ch)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        cat = categoria_de(tool)
        cor = CAT_CORES.get(cat, "#8a93a8")
        sin = (AJUDA.get(folder) or {}).get("sinopse") or desc
        self.setToolTip(f"<b>{_esc(name)}</b><br>{_esc(sin)}<br><i>{cat}</i>"
                        "<br><span style='color:#8a93a8'>Clique no ? para ver como usar</span>")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 10)
        lay.setSpacing(12)
        badge = QLabel(emoji, objectName="badge")
        badge.setFixedSize(46, 46)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qc = QColor(cor)
        badge.setStyleSheet(f"background: rgba({qc.red()},{qc.green()},{qc.blue()},40);")
        lay.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(3)
        larg = self.width() - 46 - 12 - 24 - (16 if fav else 0) - 22
        top = QHBoxLayout()
        top.setSpacing(4)
        nm = QLabel(QFontMetrics(F_NOME).elidedText(name, Qt.TextElideMode.ElideRight, larg), objectName="name")
        top.addWidget(nm, 1)
        if fav:
            top.addWidget(QLabel("★", objectName="star"), 0, Qt.AlignmentFlag.AlignTop)
        bh = QPushButton("?", objectName="helpbtn")
        bh.setFixedSize(20, 20)
        bh.setCursor(Qt.CursorShape.WhatsThisCursor)
        bh.setToolTip("Como usar")
        bh.setStyleSheet("QPushButton#helpbtn{border-radius:10px;padding:0;font-weight:bold;font-size:12px;"
                         "background:rgba(124,92,255,60);color:#e6e9f2;border:none;}"
                         "QPushButton#helpbtn:hover{background:#7c5cff;}")
        bh.clicked.connect(self.show_help)
        top.addWidget(bh, 0, Qt.AlignmentFlag.AlignTop)
        col.addLayout(top)
        d = QLabel(elide_linhas(desc, F_DESC, self.width() - 46 - 12 - 24, 3), objectName="desc")
        d.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        col.addWidget(d, 1)
        cl = QLabel(cat.split(" ", 1)[-1], objectName="catlbl")
        cl.setStyleSheet(f"color:{cor};")
        col.addWidget(cl)
        if not self.exists:
            col.addWidget(QLabel("não encontrada", objectName="missing"))
        lay.addLayout(col, 1)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.caixa.open_tool(self)

    def show_help(self):
        emoji, name, desc, folder, _ = self.tool
        AjudaDialog(name, emoji, desc, folder, self.window()).exec()

    def _menu(self, pos):
        m = QMenu(self)
        a_help = m.addAction("❓ Como usar")
        is_fav = self.key in self.caixa.cfg["favorites"]
        a_fav = m.addAction("☆ Tirar dos favoritos" if is_fav else "⭐ Favoritar")
        a_folder = m.addAction("Abrir pasta")
        a_rm = None
        if any(self.key == t[3] for t in self.caixa.extra_tools):
            a_rm = m.addAction("Remover da Caixa")
        act = m.exec(self.mapToGlobal(pos))
        if act is a_help:
            self.show_help()
        elif act is a_fav:
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
        # a janela principal é QWidget: o tema novo só pinta QMainWindow/QDialog → ficava clara (1.5.8)
        self.setObjectName("janelaCaixa")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowTitle("Caixa de Ferramentas do Caio")
        self.setWindowIcon(window_icon())
        self.resize(1280, 800)
        self.cfg = load_cfg()
        self.cfg.setdefault("favorites", [])
        self.cfg.setdefault("extra_tools", [])
        self.cfg.setdefault("uses", {})
        self.extra_tools = [tuple(t) for t in self.cfg["extra_tools"]]
        self._pagina = "hoje" if _RUMO_UI else "grade"

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(10)

        head = QHBoxLayout()
        tt = QVBoxLayout()
        tt.setSpacing(2)
        tt.addWidget(QLabel("🧰 Caixa de Ferramentas", objectName="title"))
        self.sub = QLabel("", objectName="sub")
        self.sub.setWordWrap(True)  # texto longo não pode alargar a janela (CRITICA F3)
        self.sub.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        tt.addWidget(self.sub)
        head.addLayout(tt, 1)
        self.hoje_btn = QPushButton("🏠  Hoje")
        self.hoje_btn.setCheckable(True)
        self.hoje_btn.setChecked(self._pagina == "hoje")
        self.hoje_btn.setVisible(_RUMO_UI)
        self.hoje_btn.clicked.connect(self.mostrar_hoje)
        self.todas_btn = QPushButton("🧰  Todas")
        self.todas_btn.setCheckable(True)
        self.todas_btn.setChecked(self._pagina == "grade")
        self.todas_btn.setVisible(_RUMO_UI)
        self.todas_btn.clicked.connect(self.mostrar_grade)
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
        head.addWidget(self.hoje_btn, 0, Qt.AlignmentFlag.AlignTop)
        head.addWidget(self.todas_btn, 0, Qt.AlignmentFlag.AlignTop)
        head.addWidget(self.update_btn, 0, Qt.AlignmentFlag.AlignTop)
        # boot e atalho num menu ⚙️ só: o topo cabe em 1366 px (CRITICA F3)
        self.boot_btn.hide()
        self.sc_btn.hide()
        self.mais_btn = QPushButton("⚙️")
        self.mais_btn.setToolTip("Abrir no boot / atalho no Menu Iniciar")
        menu_mais = QMenu(self.mais_btn)
        self._acao_boot = menu_mais.addAction("🔌  Abrir junto com o Windows")
        self._acao_boot.setCheckable(True)
        self._acao_boot.setChecked(self.boot_btn.isChecked())
        self._acao_boot.triggered.connect(lambda _c=False: (self.boot_btn.click(),
                                                              self._acao_boot.setChecked(self.boot_btn.isChecked())))
        menu_mais.addAction("📌  Criar atalho no Menu Iniciar").triggered.connect(lambda _c=False: self.sc_btn.click())
        self.mais_btn.setMenu(menu_mais)
        head.addWidget(self.mais_btn, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(head)

        # Barra que responde tudo (RUMO) — fica sempre no topo quando disponível
        self.barra = None
        if _RUMO_UI:
            self.barra = _caixa_busca_ui.BarraBusca(parent=self)
            self.barra.abrir_ferramenta.connect(self.open_tool_key)
            root.addWidget(self.barra)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        # Página 0: Hoje
        self.tela_hoje = None
        if _RUMO_UI:
            self.tela_hoje = _caixa_home.TelaHoje(parent=self)
            self.tela_hoje.abrir_ferramenta.connect(self.open_tool_key)
            self.tela_hoje.executar_comando.connect(self._executar_comando)
            self.tela_hoje.acao_resolvida.connect(self._acao_hoje)
            if hasattr(self.tela_hoje, "set_usos"):
                self.tela_hoje.set_usos(self.cfg.get("uses", {}))
            self.tela_hoje.pediu_todas.connect(self.mostrar_grade)
            # Hoje dentro de rolagem: a janela cabe em 1366x768 sem esmagar nada (CRITICA F3)
            self._hoje_scroll = QScrollArea()
            self._hoje_scroll.setWidgetResizable(True)
            self._hoje_scroll.setFrameShape(QFrame.Shape.NoFrame)
            self._hoje_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._hoje_scroll.setWidget(self.tela_hoje)
            self.stack.addWidget(self._hoje_scroll)
        else:
            self.stack.addWidget(QWidget())  # placeholder índice 0

        # Página 1: grade clássica
        self.pagina_grade = QWidget()
        grade_lay = QVBoxLayout(self.pagina_grade)
        grade_lay.setContentsMargins(0, 0, 0, 0)
        grade_lay.setSpacing(10)

        sr = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filtrar ferramentas na grade…")
        self.search.textChanged.connect(self.rebuild)
        sr.addWidget(self.search, 1)
        add = QPushButton("➕  Adicionar ferramenta", objectName="add")
        add.clicked.connect(self.add_tool)
        sr.addWidget(add)
        grade_lay.addLayout(sr)

        corpo = QHBoxLayout()
        corpo.setSpacing(14)
        self.side = QListWidget(objectName="side")
        self.side.setFixedWidth(230)
        self.side.currentRowChanged.connect(lambda _r: self.rebuild())
        corpo.addWidget(self.side)
        self._popular_categorias()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.host = QWidget()
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(2, 4, 2, 4)
        self.grid.setSpacing(GAP)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll.setWidget(self.host)
        corpo.addWidget(self.scroll, 1)
        grade_lay.addLayout(corpo, 1)
        self.stack.addWidget(self.pagina_grade)

        self._cols_atual = 0
        self._grade = {"card_w": CARD_W, "card_h": CARD_H, "gap": GAP, "colunas": None}
        if _RUMO_UI and _caixa_tema is not None and hasattr(_caixa_tema, "ObservadorDpi"):
            self._obs_dpi = _caixa_tema.ObservadorDpi(self)
            self._obs_dpi.dpi_mudou.connect(self._aplicar_layout_grade)
            QTimer.singleShot(0, self._obs_dpi.forcar)
        self._rt = QTimer(self)
        self._rt.setSingleShot(True)
        self._rt.setInterval(120)
        self._rt.timeout.connect(self._talvez_reflow)

        self.status = QLabel("", objectName="sub")
        root.addWidget(self.status)

        if _RUMO_UI:
            self.mostrar_hoje()
            if self.barra is not None:
                self.barra.focar()
        else:
            self.stack.setCurrentIndex(1)
            self.search.setFocus()
            self.rebuild()

        # checa atualização em segundo plano (silencioso se falhar)
        self._upd = UpdateThread()
        self._upd.found.connect(self._on_update)
        self._upd.start()

    def all_tools(self):
        return BUILTIN + self.extra_tools

    def mostrar_hoje(self):
        if not _RUMO_UI or self.tela_hoje is None:
            self.mostrar_grade()
            return
        self._pagina = "hoje"
        self.stack.setCurrentIndex(0)
        self.hoje_btn.setChecked(True)
        self.todas_btn.setChecked(False)
        self.sub.setText("O que importa no seu PC agora. Pergunte qualquer coisa na barra.")
        if self.barra is not None:
            self.barra.focar()

    def mostrar_grade(self):
        self._pagina = "grade"
        self.stack.setCurrentIndex(1)
        self.hoje_btn.setChecked(False)
        self.todas_btn.setChecked(True)
        self.search.setFocus()
        # troca a tela na hora; a grade (750 cartões, ~1 s) monta logo depois
        QTimer.singleShot(0, self.rebuild)

    def open_tool_key(self, chave: str):
        """Abre ferramenta pela chave (barra / Hoje / atalhos)."""
        chave = (chave or "").strip()
        if not chave:
            return
        # evita janela duplicada por clique duplo / sinal repetido (CRITICA F3)
        agora = time.monotonic()
        ult = getattr(self, "_ult_aberta", ("", 0.0))
        if ult[0] == chave and agora - ult[1] < 2.5:
            return
        self._ult_aberta = (chave, agora)
        tool = next((t for t in self.all_tools() if t[3] == chave), None)
        if tool is None:
            QMessageBox.warning(self, "Ops", f"Não achei a ferramenta “{chave}”.")
            return
        folder, script = tool[3], tool[4]
        path = os.path.join(BASE, folder, script)

        class _Proxy:
            pass

        proxy = _Proxy()
        proxy.tool = tool
        proxy.key = folder
        proxy.path = path
        proxy.exists = True if FROZEN else os.path.exists(path)
        self.open_tool(proxy)

    def _acao_hoje(self, acao: dict):
        """Botão da Hoje: guarda --pasta/--arquivo pra próxima abertura daquela ferramenta (se ela aceitar)."""
        chave = (acao or {}).get("chave_ferramenta") or ""
        if chave not in FERRAMENTAS_COM_ARGS:
            self._args_pendentes = None
            return
        args = list(acao.get("args") or [])
        if not args:
            if acao.get("pasta"):
                args += ["--pasta", str(acao["pasta"])]
            if acao.get("arquivo"):
                args += ["--arquivo", str(acao["arquivo"])]
        self._args_pendentes = (chave, args)

    def _executar_comando(self, comando: str):
        cmd = (comando or "").strip()
        if not cmd:
            return
        try:
            if cmd.lower().startswith("explorer"):
                subprocess.Popen(cmd, shell=True)  # noqa: S602
            elif os.path.isdir(cmd) or os.path.isfile(cmd):
                os.startfile(cmd)  # noqa: S606
            else:
                subprocess.Popen(cmd, shell=True)  # noqa: S602
            self.status.setText(f"Comando: {cmd}")
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Não deu", str(e))

    def _popular_categorias(self):
        """Lateral com Tudo, Favoritos, Novas e as categorias (com contagem)."""
        self.side.blockSignals(True)
        atual = self._cat() if self.side.count() else "__all__"
        self.side.clear()
        tools = self.all_tools()
        contagem = {}
        for t in tools:
            c = categoria_de(t)
            contagem[c] = contagem.get(c, 0) + 1
        nfav = sum(1 for t in tools if t[3] in self.cfg["favorites"])
        n_tudo = len(_caixa_arquivo.filtrar_grade_padrao(tools)) if _caixa_arquivo is not None else len(tools)
        itens = [(f"📂  Tudo  ({n_tudo})", "__all__"), (f"★  Favoritas  ({nfav})", "__fav__"),
                 ("🆕  Novas", "__new__")]
        for cname in CAT_ORDEM:
            if contagem.get(cname):
                itens.append((f"{cname}  ({contagem[cname]})", cname))
        sel = 0
        for i, (txt, data) in enumerate(itens):
            it = QListWidgetItem(txt)
            it.setData(Qt.ItemDataRole.UserRole, data)
            self.side.addItem(it)
            if data == atual:
                sel = i
        self.side.setCurrentRow(sel)
        self.side.blockSignals(False)

    def _cat(self):
        it = self.side.currentItem() if hasattr(self, "side") else None
        return it.data(Qt.ItemDataRole.UserRole) if it else "__all__"

    def _medidas_grade(self):
        lay = getattr(self, "_grade", None) or {}
        return (
            int(lay.get("card_w") or CARD_W),
            int(lay.get("card_h") or CARD_H),
            int(lay.get("gap") or GAP),
        )

    def _aplicar_layout_grade(self, _dpr, lay):
        """T20: CARD_W/H/GAP e colunas acompanham o DPI (100% ↔ 300%)."""
        global CARD_W, CARD_H, GAP
        if not isinstance(lay, dict):
            return
        CARD_W = int(lay.get("card_w") or CARD_W)
        CARD_H = int(lay.get("card_h") or CARD_H)
        GAP = int(lay.get("gap") or GAP)
        self._grade = lay
        if hasattr(self, "grid"):
            self.grid.setSpacing(GAP)
        if getattr(self, "_pagina", "") == "grade":
            self._cols_atual = -1
            self.rebuild()

    def _cols(self):
        lay = getattr(self, "_grade", None) or {}
        if lay.get("colunas"):
            return max(1, int(lay["colunas"]))
        cw, _ch, gap = self._medidas_grade()
        w = self.scroll.viewport().width() - 8
        return max(1, (w + gap) // (cw + gap))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "_rt"):
            self._rt.start()

    def _talvez_reflow(self):
        if self._cols() != self._cols_atual:
            self.rebuild()

    def _lay_section(self, title, tools, row):
        cols = self._cols()
        self._cols_atual = cols
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
        # grade escondida (tela Hoje): não monta 750 cartões à toa nem troca o subtítulo da Hoje
        if self._pagina != "grade":
            return
        q = self.search.text().lower().strip()
        cat = self._cat()
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        total = len(self.all_tools())
        tools = [t for t in self.all_tools()
                 if not q or q in t[1].lower() or q in t[2].lower()]

        # Busca: lista plana em todas as categorias (achar rápido é prioridade)
        if q:
            self._lay_section(None, tools, 0)
            self.sub.setText(f"{len(tools)} resultado(s) para “{q}”.")
            return

        favs = self.cfg["favorites"]
        uses = self.cfg["uses"]

        if cat == "__fav__":
            ft = [t for t in tools if t[3] in favs]
            self._lay_section(f"★ Favoritas  ·  {len(ft)}", ft, 0)
            self.sub.setText("Clique com o botão direito num cartão pra favoritar." if not ft
                             else f"{len(ft)} favorita(s).")
            return
        if cat == "__new__":
            nt = list(reversed(tools[-40:]))
            self._lay_section(f"🆕 Adicionadas por último  ·  {len(nt)}", nt, 0)
            self.sub.setText(f"As {len(nt)} ferramentas mais recentes da Caixa.")
            return
        # Categoria específica selecionada: mostra só ela
        if cat and cat != "__all__":
            ctools = [t for t in tools if categoria_de(t) == cat]
            self._lay_section(f"{cat}  ·  {len(ctools)}", ctools, 0)
            self.sub.setText(f"{len(ctools)} ferramenta(s) em {cat}.")
            return

        # "Tudo": agrupado — Favoritos, Mais usadas e cada categoria com seu título
        fav_tools = [t for t in tools if t[3] in favs]
        rest = [t for t in tools if t[3] not in favs]
        used = sorted([t for t in rest if uses.get(t[3], 0) > 0],
                      key=lambda t: -uses.get(t[3], 0))[:4]
        used_keys = {t[3] for t in used}
        rest = [t for t in rest if t[3] not in used_keys]
        if _caixa_arquivo is not None:
            rest = _caixa_arquivo.filtrar_grade_padrao(rest)
        row = 0
        if fav_tools:
            row = self._lay_section("★ Favoritos", fav_tools, row)
        if used:
            row = self._lay_section("🔥 Mais usadas", used, row)
        baldes = {}
        for t in rest:
            baldes.setdefault(categoria_de(t), []).append(t)
        for cname in CAT_ORDEM:
            grupo = baldes.get(cname)
            if grupo:
                row = self._lay_section(f"{cname}  ·  {len(grupo)}", grupo, row)
        self.sub.setText(f"{total} ferramentas em {sum(1 for c in CAT_ORDEM if baldes.get(c))} categorias. Clique pra abrir.")

    # ---- abrir ----
    def open_tool(self, card):
        if not card.exists:
            QMessageBox.warning(self, "Ops", f"Não achei:\n{card.path}")
            return
        try:
            os.makedirs(CFG_DIR, exist_ok=True)
            log = os.path.join(CFG_DIR, "ultima_ferramenta.log")
            pend = getattr(self, "_args_pendentes", None)
            extra = pend[1] if pend and pend[0] == card.key else []
            if MODO_TESTE:
                extra = extra + ["--teste"]
            self._args_pendentes = None
            fh = open(log, "w", encoding="utf-8")
            if FROZEN:
                # no instalador: o próprio exe abre a ferramenta (Caixa.exe --tool <chave>)
                p = subprocess.Popen([sys.executable, "--tool", card.key] + extra, stdout=fh, stderr=fh)
            else:
                p = subprocess.Popen([pythonw(), card.path] + extra, cwd=os.path.dirname(card.path),
                                     stdout=fh, stderr=fh)
            fh.close()
            msg = "Abrindo " + card.tool[1] + "…"
            self.status.setText(msg)
            # some sozinho (CRITICA F7: ficava "Abrindo…" pra sempre)
            QTimer.singleShot(7000, lambda m=msg: self.status.text() == m and self.status.setText(""))
            if os.environ.get("CAIXA_TESTE") != "1":
                self.cfg["uses"][card.key] = self.cfg["uses"].get(card.key, 0) + 1
                save_cfg(self.cfg)
                if getattr(self, "tela_hoje", None) is not None and hasattr(self.tela_hoje, "set_usos"):
                    self.tela_hoje.set_usos(self.cfg["uses"])
            if _caixa_home is not None:
                _caixa_home.salvar_ultima_chave(card.key)
            QTimer.singleShot(6000, lambda: self._checa_abriu(p, card.tool[1], log))
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Erro", str(e))

    def _checa_abriu(self, p, nome, log):
        rc = p.poll()
        if rc is None or rc == 0:
            return
        try:
            with open(log, encoding="utf-8", errors="replace") as f:
                txt = f.read()[-1500:]
        except OSError:
            txt = ""
        try:
            with open(os.path.join(CFG_DIR, "erros.log"), "a", encoding="utf-8") as f:
                f.write(f"\n=== {nome} (código {rc}) ===\n{txt}\n")
        except OSError:
            pass
        self.status.setText(f"{nome} fechou com erro. Detalhes em erros.log.")
        QMessageBox.warning(self, "A ferramenta fechou",
                            f"“{nome}” fechou logo ao abrir (código {rc}).\n\n{txt or 'Sem detalhes.'}")

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
        self._popular_categorias()
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
    if _RUMO_UI and _caixa_tema is not None:
        try:
            _caixa_tema.aplicar_tema(app)
        except Exception:
            traceback.print_exc()
            app.setStyleSheet(QSS)
    else:
        app.setStyleSheet(QSS)
    w = Caixa()
    # tamanho que cabe na tela de verdade (1080p, 768p, 4K) e centralizado
    tela = app.primaryScreen()
    if tela is not None:
        g = tela.availableGeometry()
        larg = min(1280, int(g.width() * 0.92))
        alt = min(860, int(g.height() * 0.92))
        w.setMinimumSize(min(760, larg), min(520, alt))
        w.resize(larg, alt)
        w.move(g.x() + (g.width() - larg) // 2, g.y() + (g.height() - alt) // 2)
    # bandeja + Ctrl+Espaço global (Cursor F8): fechar esconde na bandeja; menu Mostrar/Sair
    if _RUMO_UI:
        try:
            from caixa_bandeja import registrar_atalho
            w._bandeja = registrar_atalho(w)
        except Exception:  # noqa: BLE001 — sem bandeja a Caixa ainda abre normal
            traceback.print_exc()
    w.show()
    w.raise_()
    w.activateWindow()
    if getattr(w, "barra", None) is not None:
        QTimer.singleShot(150, w.barra.focar)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
