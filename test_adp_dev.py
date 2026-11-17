# -*- coding: utf-8 -*-
"""Testa os adaptadores de Dev & Dados chamando o nucleo real."""
from __future__ import annotations

import json
import unittest

import adp_dev as ad
import adp_financas as af


def _hits(texto):
    achados = []
    for item in ad.ADAPTADORES:
        if item["extrair"](texto) is not None:
            achados.append(item)
    return achados


def _um(texto, chave):
    achados = _hits(texto)
    chaves = [a["chave"] for a in achados]
    if chaves.count(chave) != 1 or any(c != chave for c in chaves):
        raise AssertionError(f"{texto!r} casou {chaves}, esperava so {chave}")
    item = next(a for a in achados if a["chave"] == chave)
    params = item["extrair"](texto)
    saida = item["calcular"](params)
    if not saida.get("resposta", "").strip() or "detalhe" not in saida:
        raise AssertionError(f"contrato invalido em {chave}: {saida!r}")
    return params, saida


class Dev(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(ad.ADAPTADORES), 30)
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])

    def test_hash(self):
        _, saida = _um("hash sha256 de caixa", "verificador-hash")
        mod = af.carregar("verificador-hash", "hsh_core")
        self.assertEqual(saida["resposta"], mod.hash_data("caixa".encode("utf-8"), "sha256"))

    def test_base64(self):
        _, saida = _um("base64 de ola", "ferramentas-dev")
        mod = af.carregar("ferramentas-dev", "fd_core")
        self.assertEqual(saida["resposta"], mod.encode_text("ola", "Base64"))

    def test_base64_decodificar(self):
        mod = af.carregar("ferramentas-dev", "fd_core")
        cod = mod.encode_text("ola", "Base64")
        _, saida = _um("decodificar base64 " + cod, "ferramentas-dev")
        self.assertEqual(saida["resposta"], mod.decode_text(cod, "Base64"))

    def test_expansao(self):
        _, saida = _um("expansao base64 90 bytes", "conversor-base64-arquivo")
        mod = af.carregar("conversor-base64-arquivo", "b64_core")
        self.assertIn(str(mod.expansao(90)["base64"]), saida["resposta"])

    def test_hexadecimal(self):
        _, saida = _um("hexadecimal de 255", "conversor-bases")
        mod = af.carregar("conversor-bases", "bse_core")
        self.assertEqual(saida["resposta"], mod.all_bases(255)["HEX"])

    def test_binario(self):
        _, saida = _um("binario de 10", "conversor-bases")
        mod = af.carregar("conversor-bases", "bse_core")
        self.assertEqual(saida["resposta"], mod.all_bases(10)["BIN"])

    def test_ieee(self):
        _, saida = _um("ieee 754 do valor 1,5", "conversor-bases")
        mod = af.carregar("conversor-bases", "bse_core")
        self.assertEqual(saida["resposta"], mod.ieee754(1.5, double=False)["hex"])

    def test_bitwise(self):
        _, saida = _um("bitwise and 15 7", "conversor-bases")
        mod = af.carregar("conversor-bases", "bse_core")
        self.assertEqual(saida["resposta"], str(mod.bitwise(15, 7, "AND")))

    def test_uuid5(self):
        _, saida = _um("uuid5 dns exemplo.com", "gerador-identificadores")
        mod = af.carregar("gerador-identificadores", "uid_core")
        self.assertEqual(saida["resposta"], mod.uuid5("DNS", "exemplo.com"))

    def test_uuid_decodificar(self):
        bruto = "550e8400-e29b-41d4-a716-446655440000"
        _, saida = _um("decodificar uuid " + bruto, "gerador-identificadores")
        mod = af.carregar("gerador-identificadores", "uid_core")
        info = mod.decode_uuid(bruto)
        self.assertIn(str(info["version"]), saida["resposta"])
        self.assertIn(info["canonical"], saida["detalhe"])

    def test_uuid4(self):
        _, saida = _um("gerar uuid4", "gerador-identificadores")
        mod = af.carregar("gerador-identificadores", "uid_core")
        self.assertEqual(mod.decode_uuid(saida["resposta"])["version"], 4)

    def test_ulid(self):
        _, saida = _um("decodificar ulid 00000000000000000000000000", "gerador-identificadores")
        mod = af.carregar("gerador-identificadores", "uid_core")
        info = mod.decode_ulid("0" * 26)
        self.assertEqual(saida["resposta"], str(info["timestamp_ms"]))

    def test_snowflake(self):
        _, saida = _um("snowflake twitter 0", "gerador-identificadores")
        mod = af.carregar("gerador-identificadores", "uid_core")
        info = mod.decode_snowflake(0, mod.EPOCHS["Twitter/X"])
        self.assertEqual(saida["resposta"], str(info["timestamp_ms"]))

    def test_colisao(self):
        _, saida = _um("colisao nanoid tamanho 4 alfabeto 16 taxa 1000", "gerador-identificadores")
        mod = af.carregar("gerador-identificadores", "uid_core")
        anos = mod.collision_years(4, 16, 1000)
        self.assertEqual(saida["resposta"], af._num(anos, 2) + " anos")

    def test_cron(self):
        expr = "0 9 * * 1"
        _, saida = _um("explicar cron " + expr, "explicador-cron")
        mod = af.carregar("explicador-cron", "crx_core")
        self.assertEqual(saida["resposta"], mod.describe(expr))

    def test_cron_proximas(self):
        expr = "0 9 * * 1"
        _, saida = _um("proximas cron " + expr, "explicador-cron")
        mod = af.carregar("explicador-cron", "crx_core")
        runs = mod.next_runs(expr, ad.INICIO_CRON, 3)
        quando = ", ".join(d.strftime("%d/%m/%Y %H:%M") for d in runs)
        self.assertEqual(saida["resposta"], quando)

    def test_sql(self):
        corpo = "select id from clientes where ativo = 1"
        _, saida = _um("formatar sql " + corpo, "formatador-sql-ast")
        mod = af.carregar("formatador-sql-ast", "sqf_core")
        self.assertEqual(saida["resposta"], mod.format_sql(corpo))

    def test_json_formatar(self):
        corpo = '{"a": 1}'
        _, saida = _um("formatar json " + corpo, "ferramentas-dev")
        mod = af.carregar("ferramentas-dev", "fd_core")
        self.assertEqual(saida["resposta"], mod.json_format(corpo))

    def test_json_minificar(self):
        corpo = '{"a": 1}'
        _, saida = _um("minificar json " + corpo, "ferramentas-dev")
        mod = af.carregar("ferramentas-dev", "fd_core")
        self.assertEqual(saida["resposta"], mod.json_minify(corpo))

    def test_json_validar(self):
        corpo = '{"a": 1}'
        _, saida = _um("validar json " + corpo, "ferramentas-dev")
        mod = af.carregar("ferramentas-dev", "fd_core")
        self.assertEqual(saida["resposta"], mod.json_validate(corpo))

    def test_schema(self):
        corpo = '{"nome": "ana"}'
        _, saida = _um("inferir schema " + corpo, "validador-json-schema")
        mod = af.carregar("validador-json-schema", "jsc_core")
        esquema = mod.infer_schema(json.loads(corpo))
        self.assertEqual(saida["resposta"], esquema["type"])

    def test_regex(self):
        _, saida = _um("regex \\d+ no texto abc 123", "inspetor-regex")
        mod = af.carregar("inspetor-regex", "rgx_core")
        r = mod.test_regex(r"\d+", "abc 123")
        self.assertEqual(saida["resposta"], str(r["match_count"]))

    def test_cidr(self):
        _, saida = _um("subrede 192.168.0.0/24", "calculadora-subrede")
        mod = af.carregar("calculadora-subrede", "ipm_core")
        self.assertIn(str(mod.analyze_cidr("192.168.0.0/24")["usable_hosts"]), saida["resposta"])

    def test_vlsm(self):
        _, saida = _um("vlsm 10.0.0.0/16 vendas 50 ti 10", "calculadora-subrede")
        mod = af.carregar("calculadora-subrede", "ipm_core")
        blocos = mod.allocate_vlsm("10.0.0.0/16", [("vendas", 50), ("ti", 10)])
        self.assertEqual(
            saida["resposta"],
            " | ".join(b["department"] + " " + b["subnet_cidr"] for b in blocos),
        )

    def test_slug(self):
        _, saida = _um("slug Acao Direta", "gerador-slug")
        mod = af.carregar("gerador-slug", "slg_core")
        self.assertEqual(saida["resposta"], mod.slugify("Acao Direta"))

    def test_path(self):
        caminho = "C:\\Users\\caio"
        _, saida = _um("converter path " + caminho, "conversor-path")
        mod = af.carregar("conversor-path", "wup_core")
        self.assertEqual(saida["resposta"], mod.convert_all(caminho)["wsl"])

    def test_toml(self):
        _, saida = _um("converter toml para json a = 1", "formatador-yaml-toml")
        mod = af.carregar("formatador-yaml-toml", "yml_core")
        self.assertEqual(saida["resposta"], mod.converter("a = 1", "toml", "json").strip())

    def test_bloom(self):
        _, saida = _um("bloom itens 1000 taxa 0,01", "filtro-bloom")
        mod = af.carregar("filtro-bloom", "blm_core")
        self.assertIn(str(mod.size_report(1000, 0.01)["m_bits"]), saida["resposta"])

    def test_pareto(self):
        _, saida = _um("pareto alpha 50 beta 30 gamma 20", "analisador-pareto")
        mod = af.carregar("analisador-pareto", "prt_core")
        r = mod.pareto_analyze(["alpha", "beta", "gamma"], [50, 30, 20])
        self.assertIn(str(r["k_for_80"]), saida["resposta"])

    def test_spline(self):
        _, saida = _um("spline 0 0 ; 1 1 ; 2 0 em 0,5", "estudio-splines")
        mod = af.carregar("estudio-splines", "spl_core")
        curva = mod.natural_cubic_spline([0, 1, 2], [0, 1, 0])
        y = mod.evaluate_spline(curva, 0.5)
        self.assertEqual(saida["resposta"], af._num(y, 4))

    def test_ciclomatica(self):
        corpo = "def f():\n    if True:\n        return 1"
        _, saida = _um("complexidade ciclomatica " + corpo, "complexidade-ciclomatica")
        mod = af.carregar("complexidade-ciclomatica", "cyc_core")
        self.assertEqual(saida["resposta"], str(mod.complexity_text(corpo)))

    def test_comentarios(self):
        corpo = "x = 1  # oi"
        _, saida = _um("remover comentarios python " + corpo, "removedor-comentarios")
        mod = af.carregar("removedor-comentarios", "scm_core")
        self.assertEqual(saida["resposta"], mod.strip_python(corpo))

    def test_carnot(self):
        _, saida = _um("carnot frio 300 quente 600", "simulador-ciclos-termodinamicos")
        mod = af.carregar("simulador-ciclos-termodinamicos", "ctm_core")
        r = mod.calcular_ciclo_carnot(300, 600)
        self.assertEqual(saida["resposta"], af._num(r["rendimento_pct"]) + "%")

    def test_otto(self):
        _, saida = _um("ciclo otto taxa 8", "simulador-ciclos-termodinamicos")
        mod = af.carregar("simulador-ciclos-termodinamicos", "ctm_core")
        r = mod.calcular_ciclo_otto(8)
        self.assertEqual(saida["resposta"], af._num(r["rendimento_pct"]) + "%")

    def test_filtro(self):
        _, saida = _um(
            "filtro digital passa baixas corte 1000 amostragem 8000",
            "laboratorio-filtros-digitais",
        )
        mod = af.carregar("laboratorio-filtros-digitais", "fdt_core")
        b, _a = mod.projetar_biquad_iir("passa_baixas", 1000, 8000)
        self.assertEqual(saida["resposta"], "b0 " + af._num(b[0], 4))

    def test_ir(self):
        _, saida = _um(
            "ir simplificado rendimento 5000 dependentes 1 inss 400",
            "calculadora-ir-simplificado",
        )
        mod = af.carregar("calculadora-ir-simplificado", "irs_core")
        r = mod.calcular_mensal(5000, 1, 400)
        self.assertEqual(saida["resposta"], mod.brl(r.ir_devido))

    def test_dissidio(self):
        _, saida = _um("dissidio salario 3000 reajuste 5% mes 3", "simulador-dissidio")
        mod = af.carregar("simulador-dissidio", "dsi_core")
        r = mod.simular(3000, 5, 3)
        self.assertEqual(saida["resposta"], mod.brl(r["salario_novo"]))

    def test_rem(self):
        _, saida = _um("ciclos rem acordar 07:00", "calculadora-ciclos-sono-rem")
        mod = af.carregar("calculadora-ciclos-sono-rem", "csr_core")
        r = mod.calcular_horarios_dormir_para_acordar("07:00")
        self.assertEqual(saida["resposta"], r["sugestoes"][0]["horario_deitar"])

    def test_cronotipo(self):
        frase = "cronotipo acordar 5 disposicao 3 dormir 4 pico 2 eu 1"
        _, saida = _um(frase, "analisador-cronotipo-sono-rotina")
        mod = af.carregar("analisador-cronotipo-sono-rotina", "cts_core")
        pontos = mod.calcular_pontuacao_meq(5, 3, 4, 2, 1)
        classe = mod.classificar_cronotipo(pontos)
        self.assertEqual(saida["resposta"], str(pontos) + " " + classe["rotulo"])

    def test_olhos(self):
        _, saida = _um("pausa olhos 8 horas as 09:00", "planejador-pausa-olhos-20-20-20")
        mod = af.carregar("planejador-pausa-olhos-20-20-20", "p20_core")
        plano = mod.planejar(8, "09:00")
        self.assertIn(str(plano.num_pausas), saida["resposta"])

    def test_postura(self):
        _, saida = _um("postura sentado 50 pausa 5 sessoes 4", "controle-postura-timer")
        mod = af.carregar("controle-postura-timer", "ptr_core")
        r = mod.gerar_plano(50, 5, 4)
        self.assertEqual(saida["resposta"], r["hora_fim_estimada"])

    def test_edital(self):
        _, saida = _um("edital dias 40 uteis 2 fim 4 topicos 20", "planejador-cronograma-estudo-edital")
        mod = af.carregar("planejador-cronograma-estudo-edital", "pce_core")
        r = mod.calcular_cronograma_edital(40, 2, 4, [{"nome": "Materia", "topicos_restantes": 20}])
        self.assertEqual(saida["resposta"], r["status_viabilidade"])

    def test_docker(self):
        corpo = "FROM python:3.12\nUSER app"
        _, saida = _um("auditar dockerfile " + corpo, "painel-docker")
        mod = af.carregar("painel-docker", "dck_core")
        self.assertIn(str(mod.audit_dockerfile(corpo)["score"]), saida["resposta"])

    def test_novos_dev_lote1(self):
        # 1. calculadora-cientifica
        _, s1 = _um("calcular expressao sin(pi/2)", "calculadora-cientifica")
        self.assertEqual(s1["resposta"], "1.0")

        # 2. gerador-gitignore
        _, s2 = _um("gerar gitignore Python", "gerador-gitignore")
        self.assertIn("regras (.gitignore)", s2["resposta"])

        # 3. gerador-gitattributes
        _, s3 = _um("gerar gitattributes EOL LF (texto)", "gerador-gitattributes")
        self.assertIn("regras (.gitattributes)", s3["resposta"])

        # 4. gerador-makefile
        _, s4 = _um("gerar makefile Python", "gerador-makefile")
        self.assertIn("linhas (Makefile)", s4["resposta"])

        # 5. gerador-dockerignore
        _, s5 = _um("gerar dockerignore Python", "gerador-dockerignore")
        self.assertIn("regras (.dockerignore)", s5["resposta"])

        # 6. gerador-pre-commit
        _, s6 = _um("gerar pre-commit Python", "gerador-pre-commit")
        self.assertIn("linhas (.pre-commit-config.yaml)", s6["resposta"])

        # 7. gerador-badges
        _, s7 = _um("gerar badge build", "gerador-badges")
        self.assertIn("img.shields.io", s7["resposta"])

        # 8. gerador-codeowners
        _, s8 = _um("gerar codeowners @dev", "gerador-codeowners")
        self.assertIn("linhas (CODEOWNERS)", s8["resposta"])

        # 9. gerador-coveragerc
        _, s9 = _um("gerar coveragerc Basico", "gerador-coveragerc")
        self.assertIn("linhas (.coveragerc)", s9["resposta"])

        # 10. gerador-eslintignore
        _, s10 = _um("gerar eslintignore Base", "gerador-eslintignore")
        self.assertIn("regras (.eslintignore)", s10["resposta"])

        # 11. gerador-github-actions
        _, s11 = _um("gerar github actions Python CI", "gerador-github-actions")
        self.assertIn("linhas (.github/workflows)", s11["resposta"])

        # 12. gerador-prettierrc
        _, s12 = _um("gerar prettierrc Padrao", "gerador-prettierrc")
        self.assertIn("linhas (.prettierrc)", s12["resposta"])

        # 13. gerador-justfile
        _, s13 = _um("gerar justfile Python", "gerador-justfile")
        self.assertIn("receitas (justfile)", s13["resposta"])

        # 14. gerador-taskfile
        _, s14 = _um("gerar taskfile Python", "gerador-taskfile")
        self.assertIn("linhas (Taskfile.yml)", s14["resposta"])

        # 15. gerador-python-version
        _, s15 = _um("gerar python-version 3.13.0", "gerador-python-version")
        self.assertEqual(s15["resposta"], "3.13.0")


if __name__ == "__main__":
    unittest.main()
