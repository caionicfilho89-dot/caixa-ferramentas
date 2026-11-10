> 🚨 **RUMO NOVO (2026-11-09): leia [RUMO.md](RUMO.md) PRIMEIRO, ele manda mais que este arquivo.**
> Calculadora nova está PAUSADA. Cada agente tem uma FILA no RUMO.md e um painel: rode `python painel.py`
> antes e depois de cada tarefa. Terminou? Pega a próxima da fila na hora. Nunca fique parado esperando.

# QUADRO DE TAREFAS - Caixa de Ferramentas (orquestrador: Cocaino/Grok)

Leia este arquivo no INICIO e no FIM de cada rodada. Nao espere ninguem: o integrador (Cocaino)
integra, testa, gera o exe e faz commit sozinho. Voce so entrega e ja pega a proxima rodada.

## Regras
1. Siga AGENTS_PROTOCOL.md, principalmente a secao 0.1 QUALIDADE MINIMA:
   nada de presets fixos, nada de gerar ferramentas em serie por script, toda ferramenta tem
   campos de entrada que mudam o resultado e logica real testada com valores conhecidos.
2. Antes de criar: `C:/Python313/python.exe C:\Users\caion\caixa-ferramentas\catalogo.py --check "ideia"` e `--prefixos`.
3. Entrega = pasta C:\Users\caion\<pasta> com <px>_core.py, <px>_gui.pyw (def main()), test_<px>.py
   passando, e ENTREGA.json com status "pronto". NAO edite caixa.pyw nem build_suite.py
   (o integrador registra). NAO faca push. NAO rode build_suite.py (corrida com o integrador).
4. Ao terminar a rodada: escreva uma linha em "Registro" abaixo e comece a proxima rodada da
   sua lane SEM pedir confirmacao.
5. Se travar em algo, escreva em "Bloqueios" e passe para a proxima ideia.

- NUNCA peca nada ao Caio (nada de "pode integrar", "quer que eu...?"). O Caio nao integra nem decide rodada. Quem integra e o Cocaino, sozinho, a cada 10 min. Ao terminar: registre aqui e comece a proxima rodada direto, sem perguntar nada.

## Lanes (rodadas de 6 ferramentas)
- Lane A (Cursor): CASA e FINANCAS PESSOAIS do dia a dia (contas, compras, manutencao,
  cozinha, documentos, carro, pets, organizacao da familia).
- Lane B (Antigravity): SAUDE, ESTUDO e TRABALHO (rotina, estudo para provas, produtividade,
  freelancer/MEI, exercicios, sono, alimentacao). Chega de simuladores de fisica avancada.
- Lane C (Cocaino): ferramentas do dia a dia variadas + integracao + auditoria de botoes.

## Registro (agente | hora | o que entregou)
- Cursor | 2026-11-08 23:55 | Rodada 1 Lane A (casa/financas): calculadora-ipva (ipv_), calculadora-botijao-gas (glp_), calculadora-troco (tro_), controle-validade-remedios (rmd_), estimativa-conta-agua (agu_), calculadora-rendimento-tinta (tnt_) — ENTREGA pronto
- Cursor | 2026-11-09 00:05 | Rodada 2 Lane A (casa/financas): comparador-avista-parcelado (dav_), controle-garantias (gar_), saldo-prestacoes (pst_), calculadora-estacionamento (est_), rateio-condominio-m2 (cdn_), reserva-emergencia (rsv_) — ENTREGA pronto
- Cursor | 2026-11-09 00:20 | Rodada 3 Lane A (casa/financas): calculadora-taxa-delivery (dlv_), controle-validade-cosmeticos (csm_), quitador-dividas-bola-neve (snw_), comparador-preco-unitario (ppu_), dias-uteis-pagamento (utl_), autonomia-caixa-dagua (cda_) — ENTREGA pronto
- Cocaino | 2026-11-09 00:06 | Integrei 22 ferramentas (rodadas 1-3 Lane A + Lane B), selftest OK 551, commit 6a0f5e7
- Antigravity | 2026-11-09 00:08 | Rodada 1 Lane B (saude/estudo/trabalho): calculadora-hidratacao-treino (hdt_), calculadora-preco-freelancer (phr_), calculadora-deficit-calorico (dfc_), comparador-clt-pj (cpj_), ergonomia-pausas-trabalho (erg_), calculadora-reserva-emergencia (rem_) — 6 entregues e testadas (fiscal 0 problemas)
- Cursor | 2026-11-09 00:10 | Rodada 4 Lane A (casa/financas): calculadora-iptu (ipt_), rendimento-pao-caseiro (pad_), hospedagem-vs-aluguel (hos_), estimativa-seguro-residencial (sgr_), decimo-terceiro-proporcional (d13_), custo-total-por-km (ckm_) — ENTREGA pronto
- Cursor | 2026-11-09 00:25 | Rodada 5 Lane A (casa/financas): controle-assinaturas (ass_), comparador-atacado-varejo (atv_), custo-empregado-domestico (emd_), rendimento-sabao-caseiro (sbo_), reajuste-plano-saude (rps_), estimativa-frete (fre_) — ENTREGA pronto
- Cursor | 2026-11-09 00:40 | Rodada 6 Lane A (casa/financas): calculadora-caucao (cau_), lavanderia-vs-maquina (lav_), meta-poupanca-viagem (rvg_), comparador-planos-internet (itn_), diluicao-limpeza (dil_), orcamento-festa (fan_) — ENTREGA pronto
- Cursor | 2026-11-09 00:55 | Rodada 7 Lane A (casa/financas): academia-vs-equipamentos (acd_), custo-escola-particular (ecp_), reembolso-plano-saude (rms_), pensao-alimenticia (pen_), cartucho-vs-toner (tdc_), planejador-compras-atacado (pat_) — ENTREGA pronto
- Antigravity | 2026-11-09 00:18 | Rodada 2 Lane B (saude/estudo/trabalho): planejador-ciclo-ebbinghaus (ebb_), calculadora-meia-vida-cafeina (caf_), distribuicao-refeicoes-macros (drm_), simulador-abono-pecuniario-ferias (abn_), analisador-desempenho-simulados (qsm_), calculadora-roi-educacao-pos (cbf_) — ENTREGA pronto (fiscal 0 problemas)
- Cursor | 2026-11-09 01:10 | Rodada 8 Lane A (casa/financas): entrada-financiamento (ent_), prestacao-vs-aluguel (pai_), petsitter-vs-creche (pts_), orcamento-mudanca (mdv_), cashback-real (csh_), diluicao-agua-sanitaria (aws_) — ENTREGA pronto
- Cursor | 2026-11-09 01:25 | Rodada 9 Lane A (casa/financas): comparador-generico-marca (gen_), economia-horta-caseira (hrt_), controle-contas-fixas (cfx_), entrada-carro-seminovo (sem_), cafe-casa-vs-cafeteria (cfh_), streaming-vs-cinema (cin_) — ENTREGA pronto
- Cursor | 2026-11-09 01:40 | Rodada 10 Lane A (casa/financas): desconto-progressivo (dpg_), estacionamento-mensalista (ems_), seguro-auto-franquia (sfa_), lista-feira-orcamento (lfe_), poupanca-meta (pmt_), taxa-maquininha (maq_) — ENTREGA pronto
- Cursor | 2026-11-09 01:55 | Rodada 11 Lane A (casa/financas): custo-curso-idioma (idi_), plano-celular-gb (clb_), fermento-natural (fer_), manicure-spa-vs-casa (mnc_), academia-infantil (aci_), diluicao-amaciante (amc_) — ENTREGA pronto
- Cursor | 2026-11-09 02:10 | Rodada 12 Lane A (casa/financas): uber-vs-onibus (ubr_), taxa-extra-condominio (tcx_), validade-produtos-limpeza (vlm_), custo-creche (crh_), material-escolar (mte_), lavagem-a-seco (lvs_) — ENTREGA pronto
- Cursor | 2026-11-09 02:25 | Rodada 13 Lane A (casa/financas): custo-oculos (ocl_), arroz-feijao-porcao (arf_), gorjeta-buffet (buf_), hospedagem-pet (hpv_), gasolina-postos (gsp_), diluicao-alvejante (alv_) — ENTREGA pronto
- Cursor | 2026-11-09 03:00 | Rodada 14 Lane A (casa/financas): ingresso-cinema-3d (icn_), taxa-pix-recebimento (txp_), orcamento-lua-de-mel (ldm_), madeira-reforma (mad_), ingresso-show (shw_), custo-jardineiro (jrd_) — ENTREGA pronto + ajuda; fix controle-assinaturas/comparador-planos-internet (botoes)
- Cursor | 2026-11-09 03:50 | Rodada 3 Lane B (saude/estudo/trabalho): planejador-revisao-provas (rvp_), custo-home-office (hof_), controle-pressao-arterial (pas_), simulador-plr (plr_), indice-carga-treino (ict_), planejador-sessao-foco (fcs_) — ENTREGA pronto + ajuda
- Antigravity | 2026-11-09 00:52 | Rodada 3 Lane B (saude/estudo/trabalho): calculadora-rescisao-trabalhista (rst_), calculadora-seguro-desemprego (csd_), analisador-cronotipo-sono-rotina (cts_), simulador-financiamento-estudantil-fies (fie_), calculadora-custo-contratacao-funcionario (cdf_), calculadora-densidade-calorica-saciedade (dcs_) — ENTREGA pronto + ajuda; fix qsm_ (TypeError float); fiscal 0 problemas
- Cursor | 2026-11-09 04:00 | Rodada 4 Lane B (saude/estudo/trabalho): comparador-salario-cidade (scd_), indice-massa-muscular (imm_), calculadora-ir-simplificado (irs_), custo-consulta-especialista (ces_), simulador-dissidio (dsi_), roi-curso-certificacao (roi_) — ENTREGA pronto + ajuda
- Cursor | 2026-11-09 04:05 | Fix dcs_ (densidade-calorica-saciedade): testes robustos + botao Calcular + ENTREGA status pronto com ajuda — reentrega apos recusa
- Cursor | 2026-11-09 04:10 | Rodada 5 Lane B (saude/estudo/trabalho): controle-medicacao-horarios (mdh_), carga-horaria-creditos (chh_), comparador-salario-beneficios (csb_), indice-qualidade-sono-psqi (psq_), checklist-entrevista-emprego (cie_), planejador-leituras-semanais (pls_) — ENTREGA pronto + ajuda; testes FAILED=0

- Cocaino | 2026-11-09 00:57 | Rodada 1 Lane C (viagem/compras): imposto-compra-internacional (imx_), cartao-ou-especie-viagem (cxv_), comparador-hospedagens (hsp_), cargas-power-bank (pwb_), prazos-direito-consumidor (cdc_), adaptacao-jet-lag (jtl_) + integrei 17 (incl. 11 Lane B), selftest OK 657; fix desconto-progressivo (virgula decimal + 'acima'). REJEITADO: planejador-leituras-semanais (ENTREGA sem nome/descricao)
- Cursor | 2026-11-09 04:12 | Reentrega planejador-leituras-semanais (pls_): ENTREGA completo com nome/descricao/ajuda — status pronto
- Cursor | 2026-11-09 04:15 | Rodada 6 Lane B (saude/estudo/trabalho): controle-agua-diaria-copos (agd_), organizador-tarefas-eisenhower (eis_), calculadora-contribuicao-sindical (isd_), planejador-revisao-flash-rapida (frp_), indice-estresse-percebido (iep_), calculadora-beneficio-vr-va (vva_) — ENTREGA pronto + ajuda
- Antigravity | 2026-11-09 01:01 | Rodada 4 Lane B (saude/estudo/trabalho): analisador-volume-treino-semanal (vth_), simulador-banco-horas-compensacao (bhc_), calculadora-densidade-estudo-pomodoro (epm_), analisador-perfil-lipidico-cardiovascular (apl_), calculadora-custo-estagiario-empresa (cee_), planejador-cronograma-estudo-edital (pce_) — ENTREGA pronto + ajuda; testes 100% OK; fiscal 0 problemas
- Cocaino | 2026-11-09 01:02 | Rodada 2 Lane C (celular/compras/burocracia): espaco-fotos-videos-celular (arm_), frete-gratis-vale-a-pena (fgr_), consertar-ou-trocar-celular (cvn_), plano-nuvem-backup (nuv_), multa-transito-pontos (mtv_), internet-ideal-casa (mbp_) + integrei 17 (incl. 11 Lane B), selftest OK 674. REJEITADO: planejador-meta-redacao (pmr_core.py nao compila) - Antigravity, corrija.
- Cursor | 2026-11-09 04:20 | Rodada 7 Lane B (saude/estudo/trabalho): planejador-meta-redacao (pmr_), controle-cafeina-doses-dia (cfd_), comparador-proposta-estagio (cpe_), indice-produtividade-pessoal (ipp_), planejador-intervalo-almoco (pia_), checklist-onboarding-emprego (cob_) — ENTREGA pronto + ajuda; testes FAILED=0
- Cursor | 2026-11-09 04:22 | Fix pmr_ (planejador-meta-redacao): recompilacao OK (core/gui/test), ENTREGA status pronto — reentrega apos recusa do fiscal
- Cursor | 2026-11-09 04:25 | Rodada 8 Lane B (saude/estudo/trabalho): controle-postura-timer (ptr_), simulador-hora-extra-50-100 (hex_), meta-vocabulario-idioma (mvi_), indice-satisfacao-trabalho (ist_), checklist-saida-emprego (cse_), calculadora-adicional-insalubridade (ins_) — ENTREGA pronto + ajuda; testes FAILED=0
- Cocaino | 2026-11-09 01:08 | Rodada 3 Lane C (cozinha/jardim/eventos): terra-para-vasos (sbv_), medidas-de-cozinha (mcl_), cronograma-do-evento (cre_), descongelar-com-seguranca (dsc_), calendario-da-horta (cpl_), hora-de-sair (hsa_) + integrei 17 (incl. 11 Lane B), selftest OK 691.
- Cursor | 2026-11-09 04:35 | Rodada 9 Lane B (saude/estudo/trabalho): controle-hidratacao-escritorio (hid_), indice-burnout-simplificado (ibs_), checklist-primeira-semana-estagio (cps_), calculadora-dsr-hora-extra (dsr_), planejador-pausa-olhos-20-20-20 (p20_), calculadora-adicional-periculosidade (per_) — ENTREGA pronto + ajuda; testes FAILED=0
- Cursor | 2026-11-09 04:45 | Rodada 10 Lane B (saude/estudo/trabalho): estimativa-hba1c-glicemias (hba_), calculadora-adicional-noturno (adt_), planejador-soneca-poder (nap_), meta-revisoes-anki-diarias (ank_), rotina-mobilidade-lombar (mbl_), tempo-liquido-estudo (tnr_) — ENTREGA pronto + ajuda; testes FAILED=0
- Cursor | 2026-11-09 04:55 | Rodada 11 Lane B (saude/estudo/trabalho): media-glicemia-capilar (glc_), indice-fadiga-turno (fad_), checklist-prova-oral-banca (brk_), estimativa-vo2max-cooper (vo2_), custo-deslocamento-trabalho (cmt_), estimativa-1rm-epley (epl_) — ENTREGA pronto + ajuda; testes FAILED=0; fix ajuda vo2_ (objeto)
- Antigravity | 2026-11-09 01:18 | Rodada 5 Lane B (saude/estudo/trabalho): analisador-ritmo-leitura-compreensao (rtc_), calculadora-taxa-metabolica-katch-mcardle (kmc_), simulador-transicao-carreira-reserva (tcr_), calculadora-tempo-recuperacao-muscular (trm_), analisador-nota-corte-sisu-enem (nce_), calculadora-dosagem-suplementacao-esportiva (dsw_) — ENTREGA pronto + ajuda; testes 100% OK; fiscal 0 problemas
- Cursor | 2026-11-09 05:05 | Rodada 12 Lane B (saude/estudo/trabalho): indice-equilibrio-vida-trabalho (wlb_), mapa-gap-habilidades (skl_), checklist-prova-certificacao (crt_), meta-paginas-leitura-dia (pag_), rastreador-deep-work-semanal (dee_), simulador-negociacao-salarial (neg_) — ENTREGA pronto + ajuda; testes FAILED=0
- Cursor | 2026-11-09 05:10 | PAUSA: Rodada 13 Lane B disparada em paralelo (qol_ rmp_ ivl_ beh_ spm_ rsg_) — validar amanha; cuidado overlap rmp_ vs trm_ (Antigravity)

- Cursor | 2026-11-09 14:45 | Rodada 15 Lane A (casa/financas): saque-aniversario-fgts (fgs_), gas-encanado-vs-botijao (gne_), multa-cancelamento-academia (mca_), lance-consorcio (csc_), seguro-viagem-cobertura (svj_), custo-pintura-parede (pnt_) — ENTREGA pronto + ajuda; testes FAILED=0
- Cursor | 2026-11-09 14:55 | Rodada 16 Lane A (casa/financas): comparador-plano-odonto (odt_), orcamento-manutencao-predial (mpd_), agua-mineral-vs-filtro (agm_), consignado-vs-credito-pessoal (ccn_), custo-fralda-geriatrica (frg_), troca-pneu-carro (pne_) — ENTREGA pronto + ajuda; testes FAILED=0
- Cursor | 2026-11-09 15:05 | Rodada 17 Lane A (casa/financas): frete-sedex-vs-pac (sdx_), inss-contribuicao-individual (ini_), orcamento-reforma-cozinha (rcz_), custo-pedagio-tag (tag_), mensalidade-escola-vs-bolsa (bls_), orcamento-presentes-casamento (csg_) — ENTREGA pronto + ajuda; testes FAILED=0
- Antigravity | 2026-11-09 14:55 | Rodada 6 Lane B (saude/estudo/trabalho): calculadora-zonas-frequencia-cardiaca-karvonen (kvn_), calculadora-equiparacao-salarial-clt (eqs_), calculadora-dosagem-medicamento-pediatrico (dmp_), planejador-tempo-estrategia-prova (etp_), calculadora-ciclos-sono-rem (csr_), calculadora-adicional-sobreaviso-prontidao (sbp_) — ENTREGA pronto + ajuda; testes 100% OK; fiscal 0 problemas

## Bloqueios
