"""Empacota a Caixa + as 16 ferramentas num executável único (Caixa.exe) com PyInstaller.

Como funciona o exe gerado:
  Caixa.exe              -> abre a Caixa (grade de ferramentas)
  Caixa.exe --tool <k>   -> abre a ferramenta <k> (a Caixa chama isso ao clicar num cartão)
  Caixa.exe --selftest   -> importa todas as ferramentas e sai (teste de sanidade do build)

Passos: (1) junta todos os .py/.pyw das pastas das ferramentas num diretório "staged" plano
(os imports são achatados, ex. 'import finder'); (2) gera o entry app.py com o mapa de
ferramentas; (3) roda o PyInstaller (onedir, --windowed).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
STAGED = os.path.join(HERE, "staged")

# chave (pasta) -> script .pyw principal
TOOLS = {
    "kit-pdf": "kit_pdf.pyw",
    "faxina-disco": "faxina.pyw",
    "recupera-arquivos": "recupera.pyw",
    "limpa-metadados": "limpar_metadados.pyw",
    "qrcode-tool": "qrcode_tool.pyw",
    "print-anotador": "print_anotador.pyw",
    "conversor-imagens": "conversor_imagens.pyw",
    "cofre-senhas": "cofre_senhas.pyw",
    "gravador-tela": "gravador_tela.pyw",
    "conversor-av": "conversor_av.pyw",
    "capturador-cores": "capturador_cores.pyw",
    "extrator-texto": "extrator_texto.pyw",
    "busca-arquivos": "busca_arquivos.pyw",
    "renomeador": "renomeador.pyw",
    "area-transferencia": "area_transferencia.pyw",
    "rastreador-tempo": "rastreador_tempo.pyw",
    "gps-falso": "gps_falso.pyw",
    "ferramentas-br": "ferramentas_br.pyw",
    "kit-hacker": "kit_hacker.pyw",
    "ferramentas-dev": "ferramentas_dev.pyw",
    "calculadora-clt": "calculadora_clt.pyw",
    "conversor-unidades": "conversor_unidades.pyw",
    "pix-boleto": "pix_boleto.pyw",
    "financas": "financas.pyw",
    "tempo": "tempo.pyw",
    "notas-md": "notas.pyw",
    "tarefas": "tarefas.pyw",
    "calendario-br": "calendario_br.pyw",
    "monitor-sistema": "monitor_sistema.pyw",
    "info-pc": "info_pc.pyw",
    "inicializacao": "inicializacao.pyw",
    "compactador": "compactador.pyw",
    "cripto-arquivos": "cripto_arquivos.pyw",
    "editor-imagem": "editor_imagem.pyw",
    "gravador-voz": "gravador_voz.pyw",
    "paletas": "paletas_cores.pyw",
    "webcam": "webcam_foto.pyw",
    "fontes": "visualizador_fontes.pyw",
    "rede": "ferramentas_rede.pyw",
    "sorteios": "sorteios.pyw",
    "saude": "saude.pyw",
    "calculadora-cientifica": "calculadora_cientifica.pyw",
    "flashcards": "flashcards.pyw",
    "visualizador-planilhas": "visualizador_planilhas.pyw",
    "orcamentos": "orcamentos.pyw",
    "contatos": "contatos.pyw",
    "leitor-ebooks": "leitor_ebooks.pyw",
    "organizador-downloads": "organizador.pyw",
    "cliente-api": "cliente_api.pyw",
    "visualizador-sqlite": "visualizador_sqlite.pyw",
    "cabecalhos-seguranca": "cabecalhos_seguranca.pyw",
    "certificado-ssl": "certificado_ssl.pyw",
    "caderno-python": "caderno_python.pyw",
    "treino-digitacao": "treino_digitacao.pyw",
    "sudoku": "sudoku.pyw",
    "metronomo": "metronomo.pyw",
    "relogio-mundial": "relogio_mundial.pyw",
    "quiz-geografia": "quiz_geografia.pyw",
    "janelas": "janelas.pyw",
    "volume-apps": "volume_apps.pyw",
    "comparar-pastas": "comparar_pastas.pyw",
    "variaveis-ambiente": "variaveis_ambiente.pyw",
    "galeria-fotos": "galeria_fotos.pyw",
    "curriculo-pdf": "curriculo_pdf.pyw",
    "etiquetas": "etiquetas.pyw",
    "analisador-texto": "analisador_texto.pyw",
    "texto-fala": "texto_fala.pyw",
    "player-musica": "player_musica.pyw",
    "autenticador-2fa": "fa_gui.pyw",
    "controle-gastos": "cg_gui.pyw",
    "receitas": "rc_gui.pyw",
    "controle-carro": "car_gui.pyw",
    "habitos": "hb_gui.pyw",
    "site-blocker": "sb_gui.pyw",
    "duplicate-detector": "dd_gui.pyw",
    "dummy-data-generator": "gd_gui.pyw",
    "disk-analyzer": "as_gui.pyw",
    "price-monitor": "pm_gui.pyw",
    "gerador-senhas": "gs_gui.pyw",
    "conversor-moedas": "cm_gui.pyw",
    "notas-criptografadas": "nc_gui.pyw",
    "calculadora-gorjeta": "tg_gui.pyw",
    "quadro-branco": "qb_gui.pyw",
    "canivete": "canivete.pyw",
    "scanner-documentos": "scn_gui.pyw",
    "compartilhar-rede": "lan_gui.pyw",
    "editor-legendas": "lg_gui.pyw",
    "teste-hardware": "th_gui.pyw",
    "mapa-mental": "mm_gui.pyw",
    "quadro-kanban": "kb_gui.pyw",
    "auditoria-pc": "aud_gui.pyw",
    "inspetor-executavel": "dk_gui.pyw",
    "estudios-gif": "gif_gui.pyw",
    "cofre-snippets": "snip_gui.pyw",
    "leitor-rss": "rss_gui.pyw",
    "gerenciador-servicos": "svc_gui.pyw",
    "analisador-wifi": "wfi_gui.pyw",
    "auditor-seo": "seo_gui.pyw",
    "corte-chapas": "ccp_gui.pyw",
    "comparador-dados": "dfx_gui.pyw",
    "laboratorio-audio": "syn_gui.pyw",
    "gravador-macros": "mcr_gui.pyw",
    "inspetor-http": "prx_gui.pyw",
    "planetario": "ast_gui.pyw",
    "codigo-barras": "bar_gui.pyw",
    "laboratorio-quimica": "chm_gui.pyw",
    "comparador-credito": "crd_gui.pyw",
    "scanner-rede": "lsc_gui.pyw",
    "simulador-circuitos": "elt_gui.pyw",
    "laboratorio-dna": "dna_gui.pyw",
    "analisador-logs": "lga_gui.pyw",
    "estudio-rotas": "gpx_gui.pyw",
    "calculadora-matrizes": "mtx_gui.pyw",
    "gerenciador-firewall": "fwl_gui.pyw",
    "painel-docker": "dck_gui.pyw",
    "laboratorio-estatistica": "stt_gui.pyw",
    "ficha-medica": "med_gui.pyw",
    "estudio-midi": "mid_gui.pyw",
    "agendador-tarefas": "sch_gui.pyw",
    "horta-jardim": "agr_gui.pyw",
    "inspetor-processos": "prc_gui.pyw",
    "estudio-svg": "svg_gui.pyw",
    "radio-morse": "mrs_gui.pyw",
    "cubagem-cargas": "cub_gui.pyw",
    "gerador-ssh": "ssk_gui.pyw",
    "leitor-nfe": "nfe_gui.pyw",
    "estudio-xadrez": "chz_gui.pyw",
    "calculadora-subrede": "ipm_gui.pyw",
    "simulador-fisica": "fsc_gui.pyw",
    "estudio-markdown": "mdx_gui.pyw",
    "gerador-ofx": "ofx_gui.pyw",
    "gerador-ssl": "gsl_gui.pyw",
    "estudio-som": "som_gui.pyw",
    "simulador-optica": "opt_gui.pyw",
    "conversor-coordenadas": "geo_gui.pyw",
    "benchmark-pc": "bmk_gui.pyw",
    "calculadora-combinatoria": "cmb_gui.pyw",
    "estudio-cifras": "cfr_gui.pyw",
    "estudio-tipografia": "tip_gui.pyw",
    "inspetor-pcap": "pcp_gui.pyw",
    "estudio-cronometro": "crn_gui.pyw",
    "arvore-decisao": "tre_gui.pyw",
    "inspetor-regex": "rgx_gui.pyw",
    "estudio-grafos": "grf_gui.pyw",
    "simulador-logica": "lgc_gui.pyw",
    "analisador-audio-fft": "fft_gui.pyw",
    "validador-json-schema": "jsc_gui.pyw",
    "calculadora-engrenagens": "grs_gui.pyw",
    "gerador-sitemap": "stm_gui.pyw",
    "simulador-gravitacional-n-corpos": "nbd_gui.pyw",
    "calculadora-concreto-armado": "cnc_gui.pyw",
    "estudio-compressao-huffman": "huf_gui.pyw",
    "simulador-automato-celular": "cll_gui.pyw",
    "analisador-geo-ip": "gip_gui.pyw",
    "calculadora-estatistica-bayesiana": "bys_gui.pyw",
    "calculadora-churrasco": "chu_gui.pyw",
    "calculadora-combustivel-viagem": "cbv_gui.pyw",
    "calculadora-sono": "sno_gui.pyw",
    "calculadora-nutricao": "ntr_gui.pyw",
    "calculadora-ar-condicionado": "btu_gui.pyw",
    "calculadora-simples-nacional": "snl_gui.pyw",
    "flashcards-repeticao": "fla_gui.pyw",
    "simulador-pendulo-duplo": "pdl_gui.pyw",
    "gerador-paleta-cores": "pal_gui.pyw",
    "calculadora-datas": "dts_gui.pyw",
    "calculadora-fotovoltaica": "pvs_gui.pyw",
    "calculadora-eletrica-residencial": "ele_gui.pyw",
    "simulador-renda-fixa": "rfx_gui.pyw",
    "calculadora-impressao-3d": "p3d_gui.pyw",
    "calculadora-fotografia": "fot_gui.pyw",
    "visualizador-ordenacao": "srt_gui.pyw",
    "simulador-epidemias": "sir_gui.pyw",
    "gerador-escalas-trabalho": "esc_gui.pyw",
    "calculadora-baterias": "bat_gui.pyw",
    "teoria-musical": "esm_gui.pyw",
    "conversor-bases": "bse_gui.pyw",
    "simulador-aposentadoria": "apo_gui.pyw",
    "gerador-identificadores": "uid_gui.pyw",
    "contraste-wcag": "wcg_gui.pyw",
    "codigo-resistores": "res_gui.pyw",
    "numero-extenso": "ext_gui.pyw",
    "explicador-cron": "crx_gui.pyw",
    "calculadora-obra": "obr_gui.pyw",
    "decodificador-jwt": "jwt_gui.pyw",
    "calculadora-banda": "bnd_gui.pyw",
    "analisador-benford": "bnf_gui.pyw",
    "simulador-controle-pid": "pid_gui.pyw",
    "teoria-filas": "qth_gui.pyw",
    "laboratorio-crc": "crc_gui.pyw",
    "analisador-cpu-termico": "cpt_gui.pyw",
    "calculadora-financeira-black-scholes": "bsc_gui.pyw",
    "calculadora-hidraulica-tubulacoes": "hdr_gui.pyw",
    "simulador-circuitos-rc-rlc": "rlc_gui.pyw",
    "formatador-sql-ast": "sqf_gui.pyw",
    "gerador-diagramas-sequence": "seq_gui.pyw",
    "pace": "pac_gui.pyw",
    "rf-calculo": "rfc_gui.pyw",
    "juros-mora": "jmr_gui.pyw",
    "inspetor-unicode": "uni_gui.pyw",
    "simulador-monte-carlo": "mtc_gui.pyw",
    "calculadora-quaternions": "qtn_gui.pyw",
    "codificador-fonetico": "phn_gui.pyw",
    "dados-rpg": "rpg_gui.pyw",
    "navegacao": "nav_gui.pyw",
    "gestacional": "gst_gui.pyw",
    "filtro-bloom": "blm_gui.pyw",
    "estudio-splines": "spl_gui.pyw",
    "calculadora-indice-conforto": "wci_gui.pyw",
    "otimizador-mochila": "knp_gui.pyw",
    "calculadora-motores-eletricos": "mot_gui.pyw",
    "calculadora-acustica-salas": "acu_gui.pyw",
    "calculadora-transformador-potencia": "trf_gui.pyw",
    "estudio-criptografia-curvas-elipticas": "ecc_gui.pyw",
    "analisador-difusao-calor": "thm_gui.pyw",
    "validador-formato-cartao-credito": "lhn_gui.pyw",
    "pet": "pet_gui.pyw",
    "cabelo": "cab_gui.pyw",
    "rateio": "rct_gui.pyw",
    "estudio-gray-code": "gry_gui.pyw",
    "compressao-rle": "rle_gui.pyw",
    "gerador-markov": "mkv_gui.pyw",
    "fatoracao-primos": "prm_gui.pyw",
    "croche": "trc_gui.pyw",
    "tamanhos": "tam_gui.pyw",
    "festa": "fst_gui.pyw",
    "estudio-bezier": "bzr_gui.pyw",
    "token-bucket": "tok_gui.pyw",
    "conversor-temperatura-cor": "ctk_gui.pyw",
    "analisador-pareto": "prt_gui.pyw",
    "quadro-branco-colaborativo": "qc_gui.pyw",
    "diario-criptografado": "dc_gui.pyw",
    "gerador-graficos": "gg_gui.pyw",
    "calculadora-alavancagem": "alg_gui.pyw",
    "gerador-lorem": "lor_gui.pyw",
    "analisador-zipf": "zpf_gui.pyw",
    "conversor-epoch": "epc_gui.pyw",
    "calculadora-tensao-cisalhamento-mohr": "mhr_gui.pyw",
    "simulador-modulacao-am-fm": "amf_gui.pyw",
    "calculadora-redes-neurais-mlp": "mlp_gui.pyw",
    "analisador-perfil-aerodinamico-naca": "nca_gui.pyw",
    "calculadora-cinetica-quimica": "knt_gui.pyw",
    "estudio-criptografia-feistel-des": "fei_gui.pyw",
    "calculadora-cafe": "cfe_gui.pyw",
    "calculadora-cerveja": "brw_gui.pyw",
    "calculadora-trelicas-2d": "trs_gui.pyw",
    "links-ntfs": "sym_gui.pyw",
    "calculadora-aquario": "aqu_gui.pyw",
    "calculadora-flambagem-colunas-euler": "eul_gui.pyw",
    "calculadora-hidroponia": "hdp_gui.pyw",
    "calculadora-marchas-bike": "bik_gui.pyw",
    "inspetor-ads": "ads_gui.pyw",
    "planejador-mudanca": "mdc_gui.pyw",
    "analisador-circuito-ressonante-lc": "rls_gui.pyw",
    "calculadora-dinamica-orbital-hohmann": "hmn_gui.pyw",
    "calculadora-fotometria-lux-lumen": "lux_gui.pyw",
    "gerador-analisador-codigo-hdlc-crc16": "hdl_gui.pyw",
    "calculadora-dilatacao-termica-tensao": "dlt_gui.pyw",
    "analisador-difracao-raios-x-bragg": "brg_gui.pyw",
    "bingo-familia": "bng_gui.pyw",
    "calculadora-equacoes-estado-gases": "vdw_gui.pyw",
    "calculadora-pao": "pao_gui.pyw",
    "calculadora-pizza": "pzz_gui.pyw",
    "ciclo-menstrual": "cic_gui.pyw",
    "comparador-mercado": "mkt_gui.pyw",
    "consumo-energia": "kwh_gui.pyw",
    "conversor-base64-arquivo": "b64_gui.pyw",
    "detector-magic": "mag_gui.pyw",
    "diff-hex": "hxd_gui.pyw",
    "enxoval-bebe": "enx_gui.pyw",
    "extrator-icones": "ico_gui.pyw",
    "inspetor-acl": "acl_gui.pyw",
    "inspetor-pem": "pem_gui.pyw",
    "mala-viagem": "mal_gui.pyw",
    "marmitas-semana": "mmt_gui.pyw",
    "monitor-pasta": "fwt_gui.pyw",
    "placar-cartas": "plc_gui.pyw",
    "placar-truco": "tru_gui.pyw",
    "planejador-casamento": "cas_gui.pyw",
    "quem-trava-arquivo": "lok_gui.pyw",
    "rega-plantas": "reg_gui.pyw",
    "simulador-precessao-giroscopica": "gyr_gui.pyw",
    "tarefas-casa": "tcs_gui.pyw",
    "verificador-hash": "hsh_gui.pyw",
}

# pacotes que precisam ser recolhidos inteiros (dados/submódulos) pro freeze funcionar
COLLECT_ALL = ["soundcard", "winrt", "winocr", "pillow_heif", "pikepdf", "segno",
               "send2trash", "piexif", "spellchecker", "pyzipper", "psutil", "openpyxl", "certifi", "tzdata", "pycaw", "comtypes", "mutagen"]


def stage():
    if os.path.exists(STAGED):
        shutil.rmtree(STAGED)
    os.makedirs(STAGED)
    copied = {}  # nome_arquivo -> origem (pra detectar colisão)
    modmap = {}  # chave -> nome_modulo da GUI

    for folder, script in TOOLS.items():
        src_dir = os.path.join(BASE, folder)
        if not os.path.isdir(src_dir):
            raise SystemExit(f"Pasta não encontrada: {src_dir}")
        for fn in os.listdir(src_dir):
            if not fn.endswith((".py", ".pyw")):
                continue
            src = os.path.join(src_dir, fn)
            # a GUI .pyw vira <nome>.py; os motores .py ficam iguais
            dst_name = fn[:-4] + ".py" if fn.endswith(".pyw") else fn
            dst = os.path.join(STAGED, dst_name)
            data = open(src, "rb").read()
            if dst_name in copied:
                if open(dst, "rb").read() != data:
                    raise SystemExit(f"COLISÃO de nome diferente: {dst_name} "
                                     f"({copied[dst_name]} x {src})")
                continue
            open(dst, "wb").write(data)
            copied[dst_name] = src
            if fn == script:
                modmap[folder] = dst_name[:-3]  # sem .py

    # caixa
    shutil.copyfile(os.path.join(HERE, "caixa.pyw"), os.path.join(STAGED, "caixa_ui.py"))
    _write_entry(modmap)
    return modmap, sorted(m[:-3] for m in copied)


def _write_entry(modmap):
    app = '''"""Entry point empacotado da Caixa de Ferramentas."""
import os
import sys

# no exe: deixa o ffmpeg empacotado visível pras ferramentas (gravador, conversor A/V)
if getattr(sys, "frozen", False):
    base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    os.environ["PATH"] = base + os.pathsep + os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")
    _umods = os.path.join(os.path.dirname(sys.executable), "user_mods")
    if os.path.isdir(_umods) and _umods not in sys.path:
        sys.path.insert(0, _umods)

MODMAP = %r

def _tool_main(key):
    mod = MODMAP.get(key)
    if not mod:
        raise SystemExit("ferramenta desconhecida: " + str(key))
    m = __import__(mod)
    m.main()

def main():
    argv = sys.argv
    if "--tool" in argv:
        i = argv.index("--tool")
        key = argv[i + 1] if i + 1 < len(argv) else ""
        _tool_main(key)
    elif "--selftest" in argv:
        ok = []
        bad = []
        for k, mod in MODMAP.items():
            try:
                m = __import__(mod); assert callable(getattr(m, "main", None)), f"{mod} sem def main()"
                ok.append(mod)
            except Exception as e:  # noqa: BLE001
                bad.append((mod, repr(e)))
        print("OK:", len(ok))
        for mod, err in bad:
            print("FALHOU", mod, err)
        sys.exit(1 if bad else 0)
    else:
        import caixa_ui
        caixa_ui.main()

if __name__ == "__main__":
    main()
''' % (modmap,)
    open(os.path.join(STAGED, "app.py"), "w", encoding="utf-8").write(app)


def build(modmap, modules):
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--windowed",
           "--name", "Caixa", "--paths", STAGED,
           "--distpath", os.path.join(HERE, "dist"),
           "--workpath", os.path.join(HERE, "build_tmp"),
           "--specpath", HERE]
    ico = os.path.join(HERE, "caixa.ico")
    if os.path.exists(ico):
        cmd += ["--icon", ico]
    # empacota o ffmpeg (se estiver em vendor/) pras ferramentas de mídia funcionarem sozinhas
    ff = os.path.join(HERE, "vendor", "ffmpeg.exe")
    if os.path.exists(ff):
        cmd += ["--add-binary", ff + os.pathsep + "."]
    for mod in modules:
        cmd += ["--hidden-import", mod]
    for pkg in COLLECT_ALL:
        cmd += ["--collect-all", pkg]
    cmd.append(os.path.join(STAGED, "app.py"))
    print("Rodando PyInstaller…")
    r = subprocess.run(cmd)
    return r.returncode


if __name__ == "__main__":
    modmap, modules = stage()
    print("Staged:", len(modules), "módulos ·", len(modmap), "ferramentas")
    if "--stage-only" in sys.argv:
        sys.exit(0)
    rc = build(modmap, modules)
    exe = os.path.join(HERE, "dist", "Caixa", "Caixa.exe")
    print("PyInstaller rc:", rc, "| exe existe:", os.path.exists(exe))
