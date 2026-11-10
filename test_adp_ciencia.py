# -*- coding: utf-8 -*-
"""Testa os adaptadores de ciência chamando o núcleo real."""
from __future__ import annotations

import unittest

import adp_ciencia as ac
import adp_financas as af


def _hits(texto):
    return [ad for ad in ac.ADAPTADORES if ad["extrair"](texto) is not None]


def _um(texto, chave):
    achados = _hits(texto)
    chaves = [a["chave"] for a in achados]
    if chaves.count(chave) != 1 or any(c != chave for c in chaves):
        raise AssertionError(f"{texto!r} casou {chaves}, esperava só {chave}")
    ad = next(a for a in achados if a["chave"] == chave)
    params = ad["extrair"](texto)
    saida = ad["calcular"](params)
    if not saida.get("resposta", "").strip() or "detalhe" not in saida:
        raise AssertionError(f"contrato inválido em {chave}: {saida!r}")
    return params, saida


class Ciencia(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(ac.ADAPTADORES), 30)
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])

    def test_molar(self):
        _, saida = _um("massa molar H2O", "laboratorio-quimica")
        mod = af.carregar("laboratorio-quimica", "chm_core")
        esp = mod.calculate_molar_mass("H2O")
        self.assertIn(af._num(esp["molar_mass_g_mol"]), saida["resposta"])

    def test_balance(self):
        _, saida = _um("balancear H2 + O2 -> H2O", "laboratorio-quimica")
        mod = af.carregar("laboratorio-quimica", "chm_core")
        esp = mod.balance_chemical_equation("H2 + O2 -> H2O")
        self.assertIn(esp["balanced"], saida["resposta"])

    def test_divisor(self):
        _, saida = _um("divisor tensao 12 r1 1000 r2 2000", "simulador-circuitos")
        mod = af.carregar("simulador-circuitos", "elt_core")
        esp = mod.calc_voltage_divider(12, 1000, 2000)
        self.assertIn(af._num(esp["vout_unloaded"]), saida["resposta"])

    def test_555(self):
        _, saida = _um("ne555 r1 1000 r2 1000 capacitor 10", "simulador-circuitos")
        mod = af.carregar("simulador-circuitos", "elt_core")
        esp = mod.calc_ne555_astable(1000, 1000, 10)
        self.assertIn(af._num(esp["frequency_hz"]), saida["resposta"])

    def test_serie(self):
        _, saida = _um("resistores em serie ohms 100 e 200 alimentacao 12", "simulador-circuitos")
        mod = af.carregar("simulador-circuitos", "elt_core")
        esp = mod.solve_resistor_network([100, 200], 12)
        self.assertIn(af._num(esp["r_series_ohms"]), saida["resposta"])

    def test_dna(self):
        _, saida = _um("analisar dna ATGCGTAA", "laboratorio-dna")
        mod = af.carregar("laboratorio-dna", "dna_core")
        esp = mod.analyze_dna("ATGCGTAA")
        self.assertIn(af._num(esp["gc_content_pct"]), saida["resposta"])

    def test_matriz(self):
        _, saida = _um("determinante da matriz 1 2 ; 3 4", "calculadora-matrizes")
        mod = af.carregar("calculadora-matrizes", "mtx_core")
        esp = mod.analyze_square_matrix(mod.parse_matrix_text("1 2\n3 4"))
        self.assertIn(af._num(esp["determinant"]), saida["resposta"])

    def test_stats(self):
        _, saida = _um("estatistica 1 2 3 4 5", "laboratorio-estatistica")
        mod = af.carregar("laboratorio-estatistica", "stt_core")
        esp = mod.descriptive_stats([1, 2, 3, 4, 5])
        self.assertIn(af._num(esp["mean"]), saida["resposta"])

    def test_projetil(self):
        _, saida = _um("projetil velocidade 20 angulo 45", "simulador-fisica")
        mod = af.carregar("simulador-fisica", "fsc_core")
        esp = mod.simulate_projectile(20, 45)
        self.assertIn(af._num(esp["max_range_m"]), saida["resposta"])

    def test_orbita(self):
        _, saida = _um("orbita altitude 400", "simulador-fisica")
        mod = af.carregar("simulador-fisica", "fsc_core")
        esp = mod.calculate_orbital_mechanics(400)
        self.assertIn(af._num(esp["orbital_period_min"]), saida["resposta"])

    def test_snell(self):
        _, saida = _um("snell n1 1 n2 1,5 angulo 30", "simulador-optica")
        mod = af.carregar("simulador-optica", "opt_core")
        esp = mod.calculate_refraction(1, 1.5, 30)
        self.assertIn(af._num(esp["angle_refraction_deg"]), saida["resposta"])

    def test_lente(self):
        _, saida = _um("lente n 1,5 r1 20 r2 -20", "simulador-optica")
        mod = af.carregar("simulador-optica", "opt_core")
        esp = mod.calculate_lens_focal(1.5, 20, -20)
        self.assertIn(af._num(esp["diopters"]), saida["resposta"])

    def test_comb(self):
        _, saida = _um("combinacao 10 escolhe 3", "calculadora-combinatoria")
        mod = af.carregar("calculadora-combinatoria", "cmb_core")
        esp = mod.calculate_combinatorics(10, 3)
        self.assertIn(str(esp["combinations_c_n_k"]), saida["resposta"])

    def test_mega(self):
        _, saida = _um("mega sena", "calculadora-combinatoria")
        mod = af.carregar("calculadora-combinatoria", "cmb_core")
        esp = mod.calculate_lottery_odds(60, 6)
        self.assertIn(esp["odds_ratio"], saida["resposta"])

    def test_viga(self):
        _, saida = _um(
            "viga bw 15 altura 40 cobrimento 3 fck 25 fyk 500 momento 80",
            "calculadora-concreto-armado",
        )
        mod = af.carregar("calculadora-concreto-armado", "cnc_core")
        esp = mod.calculate_beam_flexure(15, 40, 3, 25, 500, 80)
        self.assertIn(af._num(esp["as_adopted_cm2"]), saida["resposta"])

    def test_huffman(self):
        _, saida = _um("huffman texto ababab", "estudio-compressao-huffman")
        mod = af.carregar("estudio-compressao-huffman", "huf_core")
        cod = mod.generate_huffman_codes(mod.build_huffman_tree("ababab"))
        esp = mod.compute_entropy_and_metrics("ababab", cod)
        self.assertIn(af._num(esp["entropy"]), saida["resposta"])

    def test_wolfram(self):
        _, saida = _um("wolfram regra 30", "simulador-automato-celular")
        mod = af.carregar("simulador-automato-celular", "cll_core")
        pop = sum(mod.simulate_wolfram_1d(30)[-1])
        self.assertIn(str(pop), saida["resposta"])

    def test_benford(self):
        _, saida = _um("benford 1 12 130 1400 2 23", "analisador-benford")
        mod = af.carregar("analisador-benford", "bnf_core")
        esp = mod.analyze_benford([1, 12, 130, 1400, 2, 23])
        self.assertIn(str(esp["mad"]), saida["resposta"])

    def test_ziegler(self):
        _, saida = _um("ziegler nichols ku 2 pu 1,5", "simulador-controle-pid")
        mod = af.carregar("simulador-controle-pid", "pid_core")
        esp = mod.ziegler_nichols_pid(2, 1.5)
        self.assertIn(af._num(esp["kp"]), saida["resposta"])

    def test_darcy(self):
        _, saida = _um("darcy vazao 2 diametro 100 comprimento 50", "calculadora-hidraulica-tubulacoes")
        mod = af.carregar("calculadora-hidraulica-tubulacoes", "hdr_core")
        esp = mod.calculate_darcy_weisbach(2, 100, 50)
        self.assertIn(esp["regime"], saida["resposta"])

    def test_rc(self):
        _, saida = _um("filtro rc resistencia 1000 capacitor 1 microfarad", "simulador-circuitos-rc-rlc")
        mod = af.carregar("simulador-circuitos-rc-rlc", "rlc_core")
        esp = mod.calculate_rc_filter(1000, 1e-6)
        self.assertIn(af._num(esp["cutoff_freq_hz"]), saida["resposta"])

    def test_rlc(self):
        _, saida = _um(
            "circuito rlc resistencia 10 indutor 0,01 capacitor 1 microfarad",
            "simulador-circuitos-rc-rlc",
        )
        mod = af.carregar("simulador-circuitos-rc-rlc", "rlc_core")
        esp = mod.calculate_rlc_series(10, 0.01, 1e-6)
        self.assertIn(af._num(esp["f0_hz"]), saida["resposta"])

    def test_pi(self):
        _, saida = _um("monte carlo pi amostras 1000", "simulador-monte-carlo")
        mod = af.carregar("simulador-monte-carlo", "mtc_core")
        esp = mod.estimate_pi(1000)
        self.assertIn(af._num(esp["pi_estimate"], 4), saida["resposta"])

    def test_quaternion(self):
        _, saida = _um("quaternion 1 0 0 0", "calculadora-quaternions")
        mod = af.carregar("calculadora-quaternions", "qtn_core")
        esp = mod.analyze(mod.q_new(1, 0, 0, 0))
        self.assertIn(af._num(esp["norm"]), saida["resposta"])

    def test_nav(self):
        _, saida = _um("distancia de sao paulo ate o rio de janeiro", "navegacao")
        astm = af.carregar("planetario", "ast_core")
        mod = af.carregar("navegacao", "nav_core")
        a = astm.CITIES_BR["São Paulo, SP"]
        b = astm.CITIES_BR["Rio de Janeiro, RJ"]
        self.assertIn(af._num(mod.haversine_km(a[0], a[1], b[0], b[1])), saida["resposta"])

    def test_ceu(self):
        _, saida = _um("nascer do sol em sao paulo", "planetario")
        mod = af.carregar("planetario", "ast_core")
        lat, lon, tz = mod.CITIES_BR["São Paulo, SP"]
        esp = mod.compute_sky_report(lat, lon, tz_offset=tz)
        self.assertIn(esp["sunrise"], saida["resposta"])

    def test_trafo(self):
        _, saida = _um("transformador potencia 100 primario 127 secundario 12", "calculadora-transformador-potencia")
        mod = af.carregar("calculadora-transformador-potencia", "trf_core")
        esp = mod.design_transformer(100, 127, 12)
        self.assertIn(str(esp["n_primary"]), saida["resposta"])

    def test_parede(self):
        _, saida = _um("parede tijolo espessura 15 cm", "analisador-difusao-calor")
        mod = af.carregar("analisador-difusao-calor", "thm_core")
        nome = "Tijolo Cerâmico Furado"
        camada = mod.WallLayer(nome, 0.15, mod.DEFAULT_MATERIALS[nome])
        esp = mod.calculate_thermal_gradient([camada])
        self.assertIn(af._num(esp["u_value"], 4), saida["resposta"])

    def test_lorem(self):
        _, saida = _um("lorem 4 palavras", "gerador-lorem")
        mod = af.carregar("gerador-lorem", "lor_core")
        self.assertIn(mod.generate_words(4), saida["resposta"])

    def test_naca(self):
        _, saida = _um("perfil naca 2412", "analisador-perfil-aerodinamico-naca")
        mod = af.carregar("analisador-perfil-aerodinamico-naca", "nca_core")
        esp = mod.generate_naca_airfoil("2412")
        self.assertIn(af._num(esp["max_camber_pct"]), saida["resposta"])

    def test_cinetica(self):
        _, saida = _um("cinetica ordem 1 concentracao 1 k 0,1", "calculadora-cinetica-quimica")
        mod = af.carregar("calculadora-cinetica-quimica", "knt_core")
        esp = mod.calculate_reaction_kinetics(1, 1, 0.1)
        self.assertIn(af._num(esp["t_half_s"]), saida["resposta"])

    def test_arrhenius(self):
        _, saida = _um("arrhenius k 0,1 t1 25 t2 35 ea 50", "calculadora-cinetica-quimica")
        mod = af.carregar("calculadora-cinetica-quimica", "knt_core")
        esp = mod.arrhenius_temperature_shift(0.1, 25, 35, 50)
        self.assertIn(af._num(esp), saida["resposta"])

    def test_trelica(self):
        _, saida = _um("trelica warren", "calculadora-trelicas-2d")
        mod = af.carregar("calculadora-trelicas-2d", "trs_core")
        esp = mod.create_warren_truss().solve()
        self.assertIn(esp.static_determinacy, saida["resposta"])

    def test_euler(self):
        _, saida = _um("flambagem circular diametro 50 comprimento 3", "calculadora-flambagem-colunas-euler")
        mod = af.carregar("calculadora-flambagem-colunas-euler", "eul_core")
        nome = "Aço Estrutural ASTM A36"
        e, sy = mod.STRUCTURAL_MATERIALS[nome]
        esp = mod.calculate_buckling(3, "Bi-articulada (Pino-Pino)", e, sy, "circular_macica", 50)
        self.assertIn(af._num(esp["p_cr_kn"]), saida["resposta"])

    def test_lc(self):
        _, saida = _um("thomson indutor 0,01 capacitor 1 microfarad", "analisador-circuito-ressonante-lc")
        mod = af.carregar("analisador-circuito-ressonante-lc", "rls_core")
        esp = mod.calculate_resonance(0.01, 1e-6)
        self.assertIn(af._num(esp["f_0_hz"]), saida["resposta"])

    def test_dilatacao(self):
        _, saida = _um("dilatacao aco comprimento 10 inicial 20 final 80", "calculadora-dilatacao-termica-tensao")
        mod = af.carregar("calculadora-dilatacao-termica-tensao", "dlt_core")
        esp = mod.calculate_thermal_expansion("Aço Estrutural / Carbono", 10, 20, 80)
        self.assertIn(af._num(esp["delta_l_free_mm"]), saida["resposta"])

    def test_bitola(self):
        _, saida = _um("bitola watts 2000 volts 127 metros 20", "calculadora-eletrica-residencial")
        mod = af.carregar("calculadora-eletrica-residencial", "ele_core")
        esp = mod.dimensionar(2000, 127, 20)
        self.assertIn(af._num(esp["secao"]), saida["resposta"])

    def test_hamming(self):
        _, saida = _um("hamming 1 0 1 1", "estudio-codigo-hamming-ecc")
        mod = af.carregar("estudio-codigo-hamming-ecc", "ham_core")
        bloco = mod.codificar_bloco_74(1, 0, 1, 1)
        self.assertIn(" ".join(str(x) for x in bloco), saida["resposta"])

    def test_reator(self):
        _, saida = _um("reator conversao 0,8 ca0 1 vazao 0,01 constante 0,1", "simulador-reatores-quimicos")
        mod = af.carregar("simulador-reatores-quimicos", "rea_core")
        esp = mod.calcular_reatores(0.8, 1, 0.01, 0.1)
        self.assertIn(af._num(esp["volume_cstr_l"]), saida["resposta"])

    def test_manning(self):
        _, saida = _um(
            "manning base 2 talude 1 declividade 0,001 rugosidade 0,015 vazao 1",
            "calculadora-canais-abertos-manning",
        )
        mod = af.carregar("calculadora-canais-abertos-manning", "can_core")
        esp = mod.analisar_canal_completo(2, 1, 0.001, 0.015, modo_entrada="vazao", valor_entrada=1)
        self.assertIn(esp["regime"], saida["resposta"])

    def test_mola(self):
        _, saida = _um("mola fio 2 externo 20 espiras 8 livre 50 forca 100", "projeto-molas-helicoidais")
        mod = af.carregar("projeto-molas-helicoidais", "mol_core")
        esp = mod.calcular_mola_compressao(2, 20, 8, 50, 100)
        self.assertIn(af._num(esp["rigidez_k_n_mm"], 3), saida["resposta"])

    def test_doppler(self):
        _, saida = _um("doppler frequencia 440 fonte 30", "simulador-efeito-doppler-mach")
        mod = af.carregar("simulador-efeito-doppler-mach", "dop_core")
        esp = mod.calcular_doppler_acustico(440, 30, 0)
        self.assertIn(af._num(esp["frequencia_percebida_hz"]), saida["resposta"])

    def test_qol(self):
        _, saida = _um(
            "qualidade de vida saude 3 sono 2 humor 3 relacoes 2 lazer 1 sentido 3",
            "indice-qualidade-vida-semanal",
        )
        mod = af.carregar("indice-qualidade-vida-semanal", "qol_core")
        esp = mod.calcular_indice_qol({
            "saude_fisica": 3, "sono": 2, "humor": 3, "relacoes": 2, "lazer": 1, "sentido": 3,
        })
        self.assertIn(str(esp.indice), saida["resposta"])

    def test_glicemia(self):
        _, saida = _um("glicemia 90 110 130", "media-glicemia-capilar")
        mod = af.carregar("media-glicemia-capilar", "glc_core")
        esp = mod.analisar("90\n110\n130")
        media = next(iter(esp["grupos"].values()))["estatisticas"]["media"]
        self.assertIn(af._num(media), saida["resposta"])

    def test_fourier(self):
        _, saida = _um(
            "transiente aco placa dimensao 20 conveccao 50 inicial 200 fluido 25 tempo 60",
            "conducao-termica-transiente-fourier",
        )
        mod = af.carregar("conducao-termica-transiente-fourier", "ftr_core")
        esp = mod.calcular_transiente_termico("Aco Carbono AISI 1010", "placa", 20, 50, 200, 25, 60)
        self.assertIn(af._num(esp["t_centro_c"]), saida["resposta"])


if __name__ == "__main__":
    unittest.main()
