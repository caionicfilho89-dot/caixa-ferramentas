# -*- coding: utf-8 -*-
"""Testa os adaptadores de Rede chamando o nucleo real."""
from __future__ import annotations

import json
import unittest

import adp_financas as af
import adp_rede as ar


def _hits(texto):
    return [a for a in ar.ADAPTADORES if a["extrair"](texto) is not None]


def _um(texto, chave):
    achados = _hits(texto)
    chaves = [a["chave"] for a in achados]
    if chaves.count(chave) != 1 or any(c != chave for c in chaves):
        raise AssertionError(f"{texto!r} casou {chaves}, esperava so {chave}")
    item = next(a for a in achados if a["chave"] == chave)
    saida = item["calcular"](item["extrair"](texto))
    if not saida.get("resposta", "").strip() or "detalhe" not in saida:
        raise AssertionError(f"contrato invalido em {chave}: {saida!r}")
    return saida


class Rede(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(ar.ADAPTADORES), 15)
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])

    def test_morse(self):
        saida = _um("morse SOS", "radio-morse")
        mod = af.carregar("radio-morse", "mrs_core")
        self.assertEqual(saida["resposta"], mod.text_to_morse("SOS"))

    def test_morse_voltar(self):
        saida = _um("morse ... --- ...", "radio-morse")
        mod = af.carregar("radio-morse", "mrs_core")
        self.assertEqual(saida["resposta"], mod.morse_to_text("... --- ..."))

    def test_nato(self):
        saida = _um("fonetico oi", "radio-morse")
        mod = af.carregar("radio-morse", "mrs_core")
        self.assertEqual(saida["resposta"], mod.text_to_nato("oi"))

    def test_antena(self):
        saida = _um("antena dipolo 14", "radio-morse")
        mod = af.carregar("radio-morse", "mrs_core")
        r = mod.calculate_antenna_and_swr(14)
        self.assertEqual(saida["resposta"], af._num(r["dipole_total_m"], 3) + " m")

    def test_crc(self):
        saida = _um("crc32 de caixa", "laboratorio-crc")
        mod = af.carregar("laboratorio-crc", "crc_core")
        self.assertEqual(saida["resposta"], mod.crc_named("caixa".encode("utf-8"), "CRC-32")["hex"])

    def test_hdlc(self):
        saida = _um("hdlc crc abc", "gerador-analisador-codigo-hdlc-crc16")
        mod = af.carregar("gerador-analisador-codigo-hdlc-crc16", "hdl_core")
        self.assertEqual(saida["resposta"], str(mod.crc16_ccitt_hdlc(b"abc")))

    def test_cesar(self):
        saida = _um("cesar deslocamento 1 texto AB", "estudio-cifras")
        mod = af.carregar("estudio-cifras", "cfr_core")
        self.assertEqual(saida["resposta"], mod.caesar_cipher("AB", 1))

    def test_atbash(self):
        saida = _um("atbash AB", "estudio-cifras")
        mod = af.carregar("estudio-cifras", "cfr_core")
        self.assertEqual(saida["resposta"], mod.atbash_cipher("AB"))

    def test_vigenere(self):
        saida = _um("vigenere chave sol texto ataque", "estudio-cifras")
        mod = af.carregar("estudio-cifras", "cfr_core")
        self.assertEqual(saida["resposta"], mod.vigenere_cipher("ataque", "sol"))

    def test_feistel(self):
        saida = _um("feistel bloco 1 chave 2", "estudio-criptografia-feistel-des")
        mod = af.carregar("estudio-criptografia-feistel-des", "fei_core")
        cifra, _ = mod.feistel_encrypt_block(1, 2)
        self.assertEqual(saida["resposta"], str(cifra))

    def test_porta(self):
        saida = _um("porta xor 1 1", "simulador-logica")
        mod = af.carregar("simulador-logica", "lgc_core")
        self.assertEqual(saida["resposta"], str(mod.evaluate_gate("XOR", 1, 1)))

    def test_ip(self):
        saida = _um("tipo do ip 192.168.0.1", "analisador-geo-ip")
        mod = af.carregar("analisador-geo-ip", "gip_core")
        self.assertEqual(saida["resposta"], mod.analyze_ip_type("192.168.0.1")["type_desc"])

    def test_jwt(self):
        mod = af.carregar("decodificador-jwt", "jwt_core")
        token = mod.sign({"alg": "HS256"}, {"sub": "ana"}, "segredo")
        saida = _um("decodificar jwt " + token, "decodificador-jwt")
        info = mod.decode(token)
        self.assertEqual(saida["resposta"], json.dumps(info["payload"], ensure_ascii=False))

    def test_rot13(self):
        saida = _um("rot13 caixa", "kit-hacker")
        mod = af.carregar("kit-hacker", "kh_core")
        self.assertEqual(saida["resposta"], mod.rot13("caixa"))

    def test_identificar_hash(self):
        digest = "d41d8cd98f00b204e9800998ecf8427e"
        saida = _um("identificar hash " + digest, "kit-hacker")
        mod = af.carregar("kit-hacker", "kh_core")
        self.assertEqual(saida["resposta"], ", ".join(mod.identify_hash(digest)))

    def test_album(self):
        saida = _um("album total 100 coladas 1-40", "album-figurinhas")
        mod = af.carregar("album-figurinhas", "alb_core")
        r = mod.status(100, mod.parse_numeros("1-40"))
        self.assertEqual(saida["resposta"], str(r["n_faltantes"]) + " faltam")

    def test_papel(self):
        saida = _um("papel de parede area 20", "papel-parede")
        mod = af.carregar("papel-parede", "ppd_core")
        self.assertIn(str(mod.rolos_papel(20)["rolos"]), saida["resposta"])

    def test_drywall(self):
        saida = _um("drywall area 12", "gesso-drywall")
        mod = af.carregar("gesso-drywall", "dry_core")
        self.assertIn(str(mod.material(12)["placas"]), saida["resposta"])

    def test_pintura(self):
        frase = "pintura area 40 demaos 2 rendimento 10 perda 10% preco 80 litros 3,6 mao 0"
        saida = _um(frase, "custo-pintura-parede")
        mod = af.carregar("custo-pintura-parede", "pnt_core")
        r = mod.calcular(40, 2, 10, 10, 80, 3.6, 0)
        self.assertEqual(saida["resposta"], "R$ " + af._num(r["total"]))

    def test_negociacao(self):
        saida = _um("negociacao bruto 5000", "simulador-negociacao-salarial")
        mod = af.carregar("simulador-negociacao-salarial", "neg_core")
        r = mod.liquido_salario(5000, 0)
        self.assertEqual(saida["resposta"], mod.formatar_brl(r["liquido"]))

    def test_certificado(self):
        saida = _um("certificado vence 01/12/2026", "certificado-ssl")
        mod = af.carregar("certificado-ssl", "ssl_core")
        dias = mod.days_left(ar.HOJE_CERT.replace(month=12, day=1), ar.HOJE_CERT)
        self.assertEqual(saida["resposta"], str(dias) + " dias")


if __name__ == "__main__":
    unittest.main()
