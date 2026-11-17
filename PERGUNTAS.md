# PERGUNTAS.md — 140 casos de teste no estilo do Caio (gabarito à mão)
Autor: Grok Bot (crítico/testador) · revisão 2026-11-10 18:14 America/Sao_Paulo (lote 3 Q121–Q140 anexado; lotes 1 e 2 preservados)

Não são citações literais do Caio: são **frases inventadas no jeito informal dele**
(abreviação, vírgula decimal, sem acento às vezes) para testar a barra.
Toda resposta abaixo foi **calculada à mão** (conferência aritmética independente; sem `_core.py`).
Meta do motor: ~50/60. Ambiguidades de produto ficam em `CRITICA.md`, não aqui.

---

## Q01
**Pergunta:** quanto e 20% de 350?
**Resposta esperada:** 70
**Conta:** 20/100 × 350 = 0,20 × 350 = 70.

## Q02
**Pergunta:** troco de 100 pra 73,50
**Resposta esperada:** 26,50
**Conta:** 100,00 − 73,50 = 26,50.

## Q03
**Pergunta:** 15% de desconto em 240 reais fica quanto?
**Resposta esperada:** 204,00
**Conta:** desconto = 0,15 × 240 = 36; preço final = 240 − 36 = 204.

## Q04
**Pergunta:** aumentou 10% em cima de 1.200, quanto fica
**Resposta esperada:** 1.320
**Conta:** aumento = 0,10 × 1.200 = 120; 1.200 + 120 = 1.320.

## Q05
**Pergunta:** regra de 3: se 5 pacotes custam 37,50 quanto saem 8
**Resposta esperada:** 60,00
**Conta:** preço unitário = 37,50 ÷ 5 = 7,50; 8 × 7,50 = 60,00.

## Q06
**Pergunta:** ipva de um carro de 60 mil com aliquota 4% (taxa so do enunciado)
**Resposta esperada:** 2.400
**Conta:** alíquota dada = 4%. 0,04 × 60.000 = 2.400. (não usei tabela legal)

## Q07
**Pergunta:** tinta: parede 3m x 4m, 2 demaos, rendimento 10 m2 por litro — quantos litros
**Resposta esperada:** 2,4 L
**Conta:** área face = 3 × 4 = 12 m²; com 2 demãos = 24 m² a cobrir; 24 ÷ 10 = 2,4 L.

## Q08
**Pergunta:** 90 dias uteis a partir de 02/01/2026, so seg-sex, sem feriado, nao conta o dia 02/01, conta a partir do proximo util
**Resposta esperada:** 08/05/2026
**Conta:** 02/01/2026 = sexta → 1º dia útil contado = 05/01/2026 (segunda). Jan/2026 a partir de 05: 20 úteis; restam 70. Fev/2026: 20 úteis; restam 50. Mar/2026: 22 úteis; restam 28. Abr/2026: 22 úteis; restam 6. Mai/2026 úteis: 01, 04, 05, 06, 07, 08 → o 6º é 08/05/2026. Conferência: 20+20+22+22 = 84; 90−84 = 6 → 08/05/2026 (corrigido; antes estava errado 07/05).

## Q09
**Pergunta:** juros simples 2% ao mes em 5.000 por 6 meses, so juros
**Resposta esperada:** 600
**Conta:** J = C × i × t = 5.000 × 0,02 × 6 = 600.

## Q10
**Pergunta:** juros compostos 1% ao mes em 1.000 por 3 meses (montante)
**Resposta esperada:** 1.030,30
**Conta:** M = 1.000 × (1,01)^3. 1,01×1,01=1,0201; ×1,01=1,030301; ×1.000 = 1.030,301 → arredonda a centavo = 1.030,30.

## Q11
**Pergunta:** 1/4 de 880
**Resposta esperada:** 220
**Conta:** 880 ÷ 4 = 220.

## Q12
**Pergunta:** converter 2,5 kg pra gramas
**Resposta esperada:** 2.500 g
**Conta:** 2,5 × 1.000 = 2.500 g.

## Q13
**Pergunta:** 3 km em metros
**Resposta esperada:** 3.000 m
**Conta:** 3 × 1.000 = 3.000 m.

## Q14
**Pergunta:** gorjeta 10% em conta de 186,00
**Resposta esperada:** gorjeta 18,60; total 204,60
**Conta:** gorjeta = 0,10 × 186,00 = 18,60; total = 186,00 + 18,60 = 204,60.

## Q15
**Pergunta:** parcelar 900 em 3x sem juros, valor de cada
**Resposta esperada:** 300
**Conta:** 900 ÷ 3 = 300.

## Q16
**Pergunta:** comprei 4 un a 12,90 cada, total?
**Resposta esperada:** 51,60
**Conta:** 4 × 12,90 = 51,60.

## Q17
**Pergunta:** sobrou 1/3 de uma pizza cortada em 8 pedacos iguais — isso equivale a quantos pedacos?
**Resposta esperada:** equivalente a 8/3 ≈ 2,67 pedaços (não é número inteiro de pedaços)
**Conta:** fração × total = (1/3) × 8 = 8/3 ≈ 2,666… Como 8 não é divisível por 3, não dá pedaços inteiros; a resposta correta é a fração 8/3 (≈2,67 pedaços-equivalentes), não arredondar para 3 nem 2 sem critério.

## Q18
**Pergunta:** 40% off em 159,90
**Resposta esperada:** 95,94
**Conta:** paga 60% do preço: 0,60 × 159,90 = 95,94.

## Q19
**Pergunta:** media de 7, 8,5 e 9
**Resposta esperada:** 8,166… ≈ 8,17 (2 casas)
**Conta:** soma = 7 + 8,5 + 9 = 24,5; média = 24,5 ÷ 3 = 8,1666… → 8,17 se arredondar ao centésimo.

## Q20
**Pergunta:** velocidade media: 120 km em 1h30
**Resposta esperada:** 80 km/h
**Conta:** 1h30 = 1,5 h; 120 ÷ 1,5 = 80 km/h.

## Q21
**Pergunta:** quanto e a metade de 2.450
**Resposta esperada:** 1.225
**Conta:** 2.450 ÷ 2 = 1.225.

## Q22
**Pergunta:** 3 ovos pra 12 pessoas, pra 20 pessoas quantos ovos (mesma proporcao)
**Resposta esperada:** 5
**Conta:** 3/12 = x/20 → x = 3 × 20 ÷ 12 = 60 ÷ 12 = 5 (inteiro; cabe em ovos).

## Q23
**Pergunta:** salario 3.200, desconto 9% (aliquota so do enunciado, nao tabela oficial)
**Resposta esperada:** desconto 288; líquido 2.912
**Conta:** desconto = 0,09 × 3.200 = 288; líquido = 3.200 − 288 = 2.912.

## Q24
**Pergunta:** botijao 13 kg a 110 reais, quanto sai o kg
**Resposta esperada:** ≈ 8,46 R$/kg
**Conta:** 110 ÷ 13 = 8,4615… → 8,46 com 2 casas.

## Q25
**Pergunta:** area de um comodo 4,5m por 3,2m
**Resposta esperada:** 14,4 m²
**Conta:** 4,5 × 3,2 = 14,4.

## Q26
**Pergunta:** pintar 14,4 m2 com rendimento 12 m2/L e 1 demao — litros
**Resposta esperada:** 1,2 L
**Conta:** 14,4 ÷ 12 = 1,2 L.

## Q27
**Pergunta:** 250 ml em litros
**Resposta esperada:** 0,25 L
**Conta:** 250 ÷ 1.000 = 0,25 L.

## Q28
**Pergunta:** troco: paguei 50 no total de 38,90
**Resposta esperada:** 11,10
**Conta:** 50,00 − 38,90 = 11,10.

## Q29
**Pergunta:** 2 horas e 45 min em minutos
**Resposta esperada:** 165 min
**Conta:** 2 × 60 + 45 = 165.

## Q30
**Pergunta:** 165 minutos em horas e minutos
**Resposta esperada:** 2 h 45 min
**Conta:** 165 = 2 × 60 + 45.

## Q31
**Pergunta:** comprei por 80 vendi por 110, lucro % sobre o custo
**Resposta esperada:** 37,5%
**Conta:** lucro = 110 − 80 = 30; 30 ÷ 80 = 0,375 = 37,5%.

## Q32
**Pergunta:** 5 mil juros simples 1,5% ao mes por 4 meses, montante
**Resposta esperada:** 5.300
**Conta:** J = 5.000 × 0,015 × 4 = 300; montante = 5.000 + 300 = 5.300.

## Q33
**Pergunta:** viagem: saida 10/03/2026 de manha, volta no fim do dia 25/03/2026 — quantos diarios de hotel se cobra cada noite dormida (10 ate 24)?
**Resposta esperada:** 15 diárias
**Conta:** noites = 24 − 10 + 1? Critério: dorme nas noites de 10→11 … até 24→25 = de 10 a 24 inclusive = 24−10+1 = 15 noites. (cenário real de hospedagem, não '25−10' solto)

## Q34
**Pergunta:** 3/5 de 450
**Resposta esperada:** 270
**Conta:** (3 × 450) ÷ 5 = 1.350 ÷ 5 = 270.

## Q35
**Pergunta:** dobrar a receita de bolo que usa 200g de farinha — farinha pra receita 2x
**Resposta esperada:** 400 g
**Conta:** 200 × 2 = 400 g.

## Q36
**Pergunta:** 150 kWh a 0,85 R$/kWh (tarifa do enunciado)
**Resposta esperada:** 127,50
**Conta:** 150 × 0,85 = 127,50.

## Q37
**Pergunta:** 12 parcelas de 189,90, total pago
**Resposta esperada:** 2.278,80
**Conta:** 12 × 189,90 = 2.278,80.

## Q38
**Pergunta:** desconto de 25 reais em produto de 199
**Resposta esperada:** 174; desconto ≈ 12,56%
**Conta:** preço = 199 − 25 = 174; percentual = 25 ÷ 199 ≈ 0,125628 ≈ 12,56%.

## Q39
**Pergunta:** 45 minutos e que fracao de 1 hora
**Resposta esperada:** 3/4 = 0,75
**Conta:** 45 ÷ 60 = 3/4 = 0,75.

## Q40
**Pergunta:** de 18C pra 27C, subiu quantos graus
**Resposta esperada:** 9 °C
**Conta:** 27 − 18 = 9.

## Q41
**Pergunta:** rateio conta 360 pra 3 pessoas iguais
**Resposta esperada:** 120 cada
**Conta:** 360 ÷ 3 = 120.

## Q42
**Pergunta:** rateio 360: joao 50%, maria 30%, ana 20%
**Resposta esperada:** João 180; Maria 108; Ana 72
**Conta:** João = 0,50 × 360 = 180; Maria = 0,30 × 360 = 108; Ana = 0,20 × 360 = 72; conferência 180+108+72=360.

## Q43
**Pergunta:** 1.234,56 + 78,9
**Resposta esperada:** 1.313,46
**Conta:** 1.234,56 + 78,90 = 1.313,46.

## Q44
**Pergunta:** 10 mil menos 12,5%
**Resposta esperada:** 8.750
**Conta:** 12,5% de 10.000 = 0,125 × 10.000 = 1.250; 10.000 − 1.250 = 8.750.

## Q45
**Pergunta:** combustivel 40 litros a 5,89 o litro
**Resposta esperada:** 235,60
**Conta:** 40 × 5,89 = 235,60.

## Q46
**Pergunta:** 40 L com consumo 12 km/L, quantos km
**Resposta esperada:** 480 km
**Conta:** 40 × 12 = 480 km.

## Q47
**Pergunta:** andei 480 km e gastei 235,60, custo por km
**Resposta esperada:** ≈ 0,49 R$/km
**Conta:** 235,60 ÷ 480 = 0,490833… → 0,49 com 2 casas.

## Q48
**Pergunta:** 2 duzias e meia de ovos — quantos ovos
**Resposta esperada:** 30
**Conta:** 1 dúzia = 12; 2,5 × 12 = 30.

## Q49
**Pergunta:** 8 trabalhadores fazem em 6 dias; 4 no mesmo ritmo em quantos dias
**Resposta esperada:** 12 dias
**Conta:** trabalho = 8 × 6 = 48 homens-dia; com 4: 48 ÷ 4 = 12 dias.

## Q50
**Pergunta:** saí da loja pagando 80 reais depois de 20% de desconto — qual era o preco cheio?
**Resposta esperada:** 100
**Conta:** 80 é 80% do cheio → cheio = 80 ÷ 0,80 = 100.

## Q51
**Pergunta:** 10 horas extras a 50% sobre hora de 20 reais (adicional do enunciado)
**Resposta esperada:** 300
**Conta:** valor da hora extra = 20 × 1,5 = 30; 10 × 30 = 300.

## Q52
**Pergunta:** 3,5 m em cm
**Resposta esperada:** 350 cm
**Conta:** 3,5 × 100 = 350 cm.

## Q53
**Pergunta:** mapa 1:100.000, 3 cm no mapa — quantos km reais
**Resposta esperada:** 3 km
**Conta:** 3 cm × 100.000 = 300.000 cm = 3.000 m = 3 km.

## Q54
**Pergunta:** 7/8 de 64
**Resposta esperada:** 56
**Conta:** 64 ÷ 8 = 8; 7 × 8 = 56.

## Q55
**Pergunta:** quanto falta pra 100% se ja tenho 73%
**Resposta esperada:** 27%
**Conta:** 100 − 73 = 27.

## Q56
**Pergunta:** gorjeta 15% numa conta de 248,00 — quanto a gorjeta e o total
**Resposta esperada:** gorjeta 37,20; total 285,20
**Conta:** 0,15 × 248,00 = 37,20; total = 248,00 + 37,20 = 285,20.

## Q57
**Pergunta:** 3 camisetas a 49,90 e frete fixo 19,90 — total da compra
**Resposta esperada:** 169,60
**Conta:** 3 × 49,90 = 149,70; + 19,90 = 169,60.

## Q58
**Pergunta:** 90 dias corridos a partir de 01/02/2026 (data final = 01/02 + 90 dias)
**Resposta esperada:** 02/05/2026
**Conta:** 01/02 + 90 d: dias restantes em fev após 01 = 27 (02–28); +31 mar = 58; +30 abr = 88; faltam 2 → 02/05/2026.

## Q59
**Pergunta:** split conta de 275,50 em 2 pessoas
**Resposta esperada:** 137,75 cada
**Conta:** 275,50 ÷ 2 = 137,75.

## Q60
**Pergunta:** tenho 16 GiB livres e cada foto ocupa ~4 MiB — quantas fotos cabem?
**Resposta esperada:** 4.096
**Conta:** unidades binárias: 16 GiB = 16 × 1024 MiB = 16.384 MiB; 16.384 ÷ 4 = 4.096 fotos. (Se fosse GB/MB decimal 16×1000/4=4.000 — aqui o enunciado usa GiB/MiB.)

---

## Resumo
- Contagem: **Q01–Q60 = 60** (todas com dados suficientes e conta)
- Correção importante: **Q08 = 08/05/2026** (não 07/05)
- Q56/Q57 antigas (ambíguas) removidas desta lista → ver CRITICA
- Q60 usa **GiB/MiB** explicitamente → 4.096
---

# Lote 2 — Q61–Q120 (dia a dia do Caio ainda não coberto no lote 1)
Autor: Grok Bot · 2026-11-10 15:45 America/Sao_Paulo

Frases no jeito informal do Caio (abreviacao, virgula decimal, as vezes sem acento).
**Gabarito calculado à mão** e conferido por script independente (`fiscal-fabrica/_gen_lote2.py`, Decimal + calendario), sem `_core.py`.
Valores de tarifa/preco **so os do enunciado** (nada de tabela real inventada).
Datas: regra declarada em cada item; dias uteis = segunda a sexta, **sem feriado**, salvo se o enunciado disser o contrario.
Temas (~7–8 cada): mercado, conta de luz, combustivel, parcelas no cartao, Pix, horas trabalhadas, receita pra mais pessoas, datas.
Meta do motor no lote 2: ~50/60.

---

## Q61
**Pergunta:** feira: 1,2 kg de banana a 6,90 o kg, quanto fica
**Resposta esperada:** 8,28
**Conta:** 1,2 × 6,90 = 8,28.

## Q62
**Pergunta:** mercado: 3 refri a 7,49 e 2 paes a 0,80 cada, total
**Resposta esperada:** 24,07
**Conta:** 3 × 7,49 = 22,47; 2 × 0,80 = 1,60; 22,47 + 1,60 = 24,07.

## Q63
**Pergunta:** promo 4 pelo preco de 3, cada um custa 5,50 — quanto saem 4
**Resposta esperada:** 16,50
**Conta:** paga 3 unidades: 3 × 5,50 = 16,50.

## Q64
**Pergunta:** leite tava 5,20 agora ta 6,24, subiu quanto por cento
**Resposta esperada:** 20%
**Conta:** aumento = 6,24 − 5,20 = 1,04; 1,04 ÷ 5,20 = 0,20 = 20%.

## Q65
**Pergunta:** lista do mercado: arroz 22,90, feijao 8,50, oleo 7,89 e sal 2,15 — total
**Resposta esperada:** 41,44
**Conta:** 22,90 + 8,50 = 31,40; + 7,89 = 39,29; + 2,15 = 41,44.

## Q66
**Pergunta:** levei 80 reais no mercado, a compra deu 63,47, quanto sobra
**Resposta esperada:** 16,53
**Conta:** 80,00 − 63,47 = 16,53.

## Q67
**Pergunta:** 1,5 kg de carne a 42,90 o kg, quanto pago
**Resposta esperada:** 64,35
**Conta:** 1,5 × 42,90 = 64,35.

## Q68
**Pergunta:** desconto de 12% numa compra de 150 no mercado, fica quanto
**Resposta esperada:** 132,00
**Conta:** 12% de 150 = 18; 150 − 18 = 132,00.

## Q69
**Pergunta:** conta de luz: 220 kWh a 0,92 R$/kWh (tarifa so do enunciado)
**Resposta esperada:** 202,40
**Conta:** 220 × 0,92 = 202,40.

## Q70
**Pergunta:** luz: 180 kWh a 0,75 mais taxa fixa de 15 reais (valores do enunciado)
**Resposta esperada:** 150,00
**Conta:** 180 × 0,75 = 135; 135 + 15 = 150,00.

## Q71
**Pergunta:** mes passado a luz foi 240 kWh, esse mes 192, caiu quanto %
**Resposta esperada:** 20%
**Conta:** queda = 240 − 192 = 48; 48 ÷ 240 = 0,20 = 20%.

## Q72
**Pergunta:** rateio da conta de luz 312,60 pra 3 casas iguais
**Resposta esperada:** 104,20 cada
**Conta:** 312,60 ÷ 3 = 104,20.

## Q73
**Pergunta:** luz 200 kWh, tarifa 0,80 mais adicional 0,05 por kWh (so do enunciado)
**Resposta esperada:** 170,00
**Conta:** 200 × 0,80 = 160; 200 × 0,05 = 10; 160 + 10 = 170,00.

## Q74
**Pergunta:** se 100 kWh da luz saem 87,00, 250 kWh na mesma tarifa ficam quanto
**Resposta esperada:** 217,50
**Conta:** tarifa = 87,00 ÷ 100 = 0,87; 250 × 0,87 = 217,50.

## Q75
**Pergunta:** parcelar a conta de luz de 189,90 em 3x iguais sem juros
**Resposta esperada:** 63,30
**Conta:** 189,90 ÷ 3 = 63,30.

## Q76
**Pergunta:** gasolina 6,19 o litro, enchi 35 L, quanto paguei
**Resposta esperada:** 216,65
**Conta:** 35 × 6,19 = 216,65.

## Q77
**Pergunta:** viagem 270 km, carro faz 15 km/L, gasolina a 6,00 (preco do enunciado) — quanto gasto
**Resposta esperada:** 108,00
**Conta:** litros = 270 ÷ 15 = 18 L; 18 × 6,00 = 108,00.

## Q78
**Pergunta:** tanque de 50 L tava com 1/4, quanto falta pra encher
**Resposta esperada:** 37,5 L
**Conta:** falta 3/4 do tanque: 0,75 × 50 = 37,5 L.

## Q79
**Pergunta:** etanol 4,29 e gasolina 6,15, etanol rende 70% da gasolina — qual vale mais a pena (precos do enunciado)
**Resposta esperada:** etanol (equivalente ≈ 6,13 < 6,15)
**Conta:** preco equivalente do etanol = 4,29 ÷ 0,70 = 6,12857… ≈ 6,13 (arredonda a 2 casas). Como 6,13 < 6,15, o etanol sai um pouco mais barato por km equivalente.

## Q80
**Pergunta:** andei 360 km com 30 L, qual o consumo em km/L
**Resposta esperada:** 12 km/L
**Conta:** 360 ÷ 30 = 12 km/L.

## Q81
**Pergunta:** ida e volta 90 km cada trecho, consumo 15 km/L, litro a 6,20 — custo da viagem
**Resposta esperada:** 74,40
**Conta:** distancia = 90 × 2 = 180 km; 180 ÷ 15 = 12 L; 12 × 6,20 = 74,40.

## Q82
**Pergunta:** 25 litros de gasolina a 5,99 o litro, total
**Resposta esperada:** 149,75
**Conta:** 25 × 5,99 = 149,75.

## Q83
**Pergunta:** falta 42 km, o carro faz 14 km/L — quantos litros preciso
**Resposta esperada:** 3 L
**Conta:** 42 ÷ 14 = 3 L.

## Q84
**Pergunta:** comprei 1.200 no cartao em 6x sem juros, valor de cada parcela
**Resposta esperada:** 200
**Conta:** 1.200 ÷ 6 = 200.

## Q85
**Pergunta:** 10x de 89,90 no cartao, quanto vou pagar no total
**Resposta esperada:** 899,00
**Conta:** 10 × 89,90 = 899,00.

## Q86
**Pergunta:** parcela de 150 por 8 meses, ja paguei 3, quanto ainda devo
**Resposta esperada:** 750
**Conta:** faltam 5 parcelas; 5 × 150 = 750.

## Q87
**Pergunta:** compra de 800 no cartao com 5% de juros no total, parcelada em 4x iguais — valor da parcela e total
**Resposta esperada:** parcela 210; total 840
**Conta:** total com juros = 800 × 1,05 = 840; parcela = 840 ÷ 4 = 210.

## Q88
**Pergunta:** fatura do cartao 1.350, paguei o minimo de 15% (percentual so do enunciado)
**Resposta esperada:** 202,50
**Conta:** 0,15 × 1.350 = 202,50.

## Q89
**Pergunta:** fatura 2.000, paguei 600, quanto sobra
**Resposta esperada:** 1.400
**Conta:** 2.000 − 600 = 1.400.

## Q90
**Pergunta:** 3 compras no cartao: 49,90 + 120,00 + 15,50, total
**Resposta esperada:** 185,40
**Conta:** 49,90 + 120,00 = 169,90; + 15,50 = 185,40.

## Q91
**Pergunta:** anuidade de 480 cobrada em 12x no cartao, quanto e por mes
**Resposta esperada:** 40
**Conta:** 480 ÷ 12 = 40.

## Q92
**Pergunta:** pix de 350 pra maria e 180 pra joao, quanto mandei no total
**Resposta esperada:** 530
**Conta:** 350 + 180 = 530.

## Q93
**Pergunta:** recebi um pix de 1.250 e mandei outro de 430, quanto ficou desses dois
**Resposta esperada:** 820
**Conta:** 1.250 − 430 = 820.

## Q94
**Pergunta:** vou dividir um pix de 97,50 pra 3 pessoas iguais
**Resposta esperada:** 32,50 cada
**Conta:** 97,50 ÷ 3 = 32,50.

## Q95
**Pergunta:** pix de 2 mil com tarifa de 1,5% (tarifa so do enunciado, nao regra real do pix) — quanto cai na conta
**Resposta esperada:** 1.970,00
**Conta:** 1,5% de 2.000 = 30; 2.000 − 30 = 1.970,00.

## Q96
**Pergunta:** preciso pagar 1.080 no pix, ja mandei 400, quanto falta
**Resposta esperada:** 680
**Conta:** 1.080 − 400 = 680.

## Q97
**Pergunta:** 5 pessoas mandam 80 reais cada no pix pro churrasco, total
**Resposta esperada:** 400
**Conta:** 5 × 80 = 400.

## Q98
**Pergunta:** pix de 75,90 + 32,40 + 11,70, soma
**Resposta esperada:** 120,00
**Conta:** 75,90 + 32,40 = 108,30; + 11,70 = 120,00.

## Q99
**Pergunta:** trabalhei 8h por dia em 22 dias, quantas horas no mes
**Resposta esperada:** 176 h
**Conta:** 8 × 22 = 176 h.

## Q100
**Pergunta:** hora de 25 reais, 176 horas trabalhadas (valores do enunciado), quanto ganho
**Resposta esperada:** 4.400
**Conta:** 176 × 25 = 4.400.

## Q101
**Pergunta:** entrei 8:15 e sai 17:45, com 1h de almoco — horas liquidas
**Resposta esperada:** 8 h 30 min
**Conta:** 17:45 − 8:15 = 9 h 30 min; menos 1 h de almoco = 8 h 30 min (510 min).

## Q102
**Pergunta:** fiz 3 turnos de 6,5 h, total de horas
**Resposta esperada:** 19,5 h
**Conta:** 3 × 6,5 = 19,5 h.

## Q103
**Pergunta:** hora de 18 reais, 12 horas extras com adicional de 50% (adicional do enunciado)
**Resposta esperada:** 324
**Conta:** hora extra = 18 × 1,5 = 27; 12 × 27 = 324.

## Q104
**Pergunta:** jornada de 44h na semana, trabalhei 50h, quantas horas extras
**Resposta esperada:** 6 h
**Conta:** 50 − 44 = 6 h.

## Q105
**Pergunta:** ganho 3.520 pra 160 horas, quanto vale a hora
**Resposta esperada:** 22,00
**Conta:** 3.520 ÷ 160 = 22,00.

## Q106
**Pergunta:** receita de bolo pra 8 pessoas usa 300g de farinha; pra 12 pessoas, quanta farinha
**Resposta esperada:** 450 g
**Conta:** fator 12 ÷ 8 = 1,5; 300 × 1,5 = 450 g.

## Q107
**Pergunta:** molho pra 4 pessoas leva 2 dentes de alho; pra 10 pessoas, quantos dentes
**Resposta esperada:** 5 dentes
**Conta:** 2 × (10 ÷ 4) = 2 × 2,5 = 5 dentes.

## Q108
**Pergunta:** pudim pra 6 usa 1 lata de leite; pra 9 pessoas, quantas latas
**Resposta esperada:** 1,5 lata
**Conta:** 9 ÷ 6 = 1,5 lata.

## Q109
**Pergunta:** suco: 3 laranjas pra 2 pessoas, pra 8 pessoas quantas laranjas
**Resposta esperada:** 12 laranjas
**Conta:** 3 × (8 ÷ 2) = 3 × 4 = 12.

## Q110
**Pergunta:** a receita pede 500 ml de agua pra 4 pessoas; pra 6, quantos ml
**Resposta esperada:** 750 ml
**Conta:** 500 × (6 ÷ 4) = 500 × 1,5 = 750 ml.

## Q111
**Pergunta:** 250g de macarrao pra 2 pessoas, pra 5 pessoas quanto de macarrao
**Resposta esperada:** 625 g
**Conta:** 250 × (5 ÷ 2) = 250 × 2,5 = 625 g.

## Q112
**Pergunta:** a receita original rende 6 porcoes, eu quero 18 — multiplica por quanto
**Resposta esperada:** 3 vezes (triplicar)
**Conta:** 18 ÷ 6 = 3.

## Q113
**Pergunta:** 15/11/2026 cai em que dia da semana
**Resposta esperada:** domingo
**Conta:** regra: calendario gregoriano civil (Python datetime). 15/11/2026 = domingo. Nao usa feriado nesta pergunta (so o dia da semana).

## Q114
**Pergunta:** 10 dias corridos a partir de 20/03/2026, nao conta o dia 20, soma 10 dias
**Resposta esperada:** 30/03/2026
**Conta:** regra: dias corridos, 20/03 + 10 = 30/03/2026 (segunda-feira). Nao desconta fim de semana nem feriado.

## Q115
**Pergunta:** quantos dias corridos de 01/04/2026 ate 15/04/2026, incluindo o primeiro e o ultimo
**Resposta esperada:** 15 dias
**Conta:** regra: inclusivo nos dois extremos. 15 − 1 + 1 = 15 dias.

## Q116
**Pergunta:** 15 dias uteis a partir de 02/03/2026, so seg-sex, sem feriado, nao conta o dia 02/03, conta a partir do proximo util
**Resposta esperada:** 23/03/2026
**Conta:** regra: uteis = segunda a sexta, **sem feriado**; nao conta 02/03/2026 (segunda) → 1º dia = 03/03/2026 (terça). Uteis: 03, 04, 05, 06, 09, 10, 11, 12, 13, 16, 17, 18, 19, 20, 23 → o 15º e 23/03/2026 (segunda).

## Q117
**Pergunta:** 01/05/2026 cai em que dia da semana
**Resposta esperada:** sexta-feira
**Conta:** regra: so dia da semana no calendario civil. 01/05/2026 = sexta-feira. (E feriado do trabalhador no Brasil, mas a pergunta pede so o dia da semana.)

## Q118
**Pergunta:** de 10/06/2026 ate 10/07/2026, quantos dias corridos (nao conta o dia inicial, conta o final: 10/06 + N = 10/07)
**Resposta esperada:** 30 dias
**Conta:** regra: diferenca de datas corridas 10/07 − 10/06 = 30 dias (junho tem 30 dias). Nao desconta fim de semana.

## Q119
**Pergunta:** 45 dias corridos a partir de 15/11/2026 (15/11 + 45, nao conta o 15)
**Resposta esperada:** 30/12/2026
**Conta:** regra: dias corridos. Restam 15 dias em novembro depois do 15 (16–30); 45 − 15 = 30 → 30/12/2026 (quarta-feira). Conferencia: date(2026,11,15) + 45 dias.

## Q120
**Pergunta:** 20 dias uteis a partir de 06/04/2026, so seg-sex, sem feriado, nao conta o dia 06/04, conta a partir do proximo util
**Resposta esperada:** 04/05/2026
**Conta:** regra: uteis = segunda a sexta, **sem feriado** (o 01/05/2026, sexta, **entra na conta** porque o enunciado exclui feriado). 06/04/2026 = segunda (nao conta) → 1º dia = 07/04/2026 (terça). Abril: 07–10 (4), 13–17 (5), 20–24 (5), 27–30 (4) = 18; restam 2: 01/05 e 04/05 → 04/05/2026 (segunda).

---

## Resumo lote 2
- Contagem: **Q61–Q120 = 60** (todas calculaveis com dados na frase; soma geral Q01–Q120 = 120)
- Distribuicao: mercado 8 (Q61–Q68), luz 7 (Q69–Q75), combustivel 8 (Q76–Q83), cartao 8 (Q84–Q91), Pix 7 (Q92–Q98), horas 7 (Q99–Q105), receita 7 (Q106–Q112), datas 8 (Q113–Q120)
- Datas conferidas por codigo; Q116 e Q120 usam regra **sem feriado** (declarada). Q120 conta 01/05/2026 de proposito, por essa regra.
- Nenhuma pergunta do lote 2 repete o enunciado do lote 1.

## Q121
**Pergunta:** aluguel 1.850, condominio 420 e agua 87,30, quanto da o mes da casa
**Resposta esperada:** 2.357,30
**Conta:** 1.850 + 420 = 2.270; 2.270 + 87,30 = 2.357,30.

## Q122
**Pergunta:** na loja de material paguei 200, a compra deu 163,40, qual o troco
**Resposta esperada:** 36,60
**Conta:** 200,00 − 163,40 = 36,60.

## Q123
**Pergunta:** piso da sala: 8,5 m2, cada caixa de ceramica rende 1,7 m2, quantas caixas preciso
**Resposta esperada:** 5
**Conta:** 8,5 ÷ 1,7 = 5 caixas.

## Q124
**Pergunta:** peguei 2.000 emprestado pra reforma da casa, juros compostos 2% ao mes por 2 meses (montante, taxa so do enunciado)
**Resposta esperada:** 2.080,80
**Conta:** M = 2.000 × (1,02)^2. 1,02 × 1,02 = 1,0404; 1,0404 × 2.000 = 2.080,80.

## Q125
**Pergunta:** o pedreiro vai 12 dias uteis a partir de 16/11/2026, so seg-sex, sem feriado, nao conta o dia 16/11, conta a partir do proximo util — que dia termina
**Resposta esperada:** 02/12/2026
**Conta:** regra: úteis = segunda a sexta, **sem feriado** (nenhum feriado é descontado). 16/11/2026 = segunda (não conta) → 1º dia = 17/11/2026 (terça). 17–20 (4), 23–27 (5), 30/11, 01/12 e 02/12 (3) = 12. Termina em 02/12/2026 (quarta-feira). Conferência por código.

## Q126
**Pergunta:** estacionamento 8,50 a hora, fiquei 3,5 h, quanto pago
**Resposta esperada:** 29,75
**Conta:** 8,50 × 3,5 = 29,75.

## Q127
**Pergunta:** oleo do carro troca a cada 10.000 km, ta com 47.800, quanto falta pra chegar nos 50.000
**Resposta esperada:** 2.200
**Conta:** 50.000 − 47.800 = 2.200 km.

## Q128
**Pergunta:** pneu 205 mm de largura, isso da quantos cm
**Resposta esperada:** 20,5 cm
**Conta:** 205 mm ÷ 10 = 20,5 cm.

## Q129
**Pergunta:** seguro do carro 2.400 no ano, quanto da por mes
**Resposta esperada:** 200
**Conta:** 2.400 ÷ 12 = 200.

## Q130
**Pergunta:** 3 pedagios de 6,40 na ida e os mesmos 3 na volta, quanto gasto de pedagio
**Resposta esperada:** 38,40
**Conta:** 3 × 6,40 = 19,20 na ida; ida + volta = 19,20 × 2 = 38,40.

## Q131
**Pergunta:** hotel 189 a diaria, 4 noites, quanto fica a hospedagem
**Resposta esperada:** 756
**Conta:** 189 × 4 = 756.

## Q132
**Pergunta:** viagem: 280 dolares a 5,40 o dolar (cambio so do enunciado), quanto e em reais
**Resposta esperada:** 1.512,00
**Conta:** 280 × 5,40 = 1.512,00.

## Q133
**Pergunta:** embarque 03/01/2027, hoje e 15/12/2026, quantos dias corridos faltam (nao conta o 15/12, conta o 03/01)
**Resposta esperada:** 19 dias
**Conta:** regra: dias corridos. 15/12/2026 + 19 = 03/01/2027. Restam 16 dias em dezembro depois do 15 (16–31) + 3 em janeiro (01–03) = 19. Conferência: date(2027,1,3) − date(2026,12,15) = 19. 03/01/2027 = domingo.

## Q134
**Pergunta:** a viagem deu 2.460 no total, somos 4, quanto cada um
**Resposta esperada:** 615
**Conta:** 2.460 ÷ 4 = 615.

## Q135
**Pergunta:** aluguel de carro 95 por dia, 3 dias de viagem, quanto e so o carro
**Resposta esperada:** 285
**Conta:** 95 × 3 = 285.

## Q136
**Pergunta:** job freela de 2.800, o cliente reteve 10% de imposto (aliquota so do enunciado), quanto cai na conta
**Resposta esperada:** 2.520,00
**Conta:** 10% de 2.800 = 280; 2.800 − 280 = 2.520,00.

## Q137
**Pergunta:** cobro 85 a hora no freela, fiz 16,5 h nesse job, quanto faturo
**Resposta esperada:** 1.402,50
**Conta:** 85 × 16,5 = 1.402,50.

## Q138
**Pergunta:** cliente atrasou um freela de 1.500, combinamos juros simples 2% ao mes por 3 meses, so os juros (taxa so do enunciado)
**Resposta esperada:** 90
**Conta:** J = 1.500 × 0,02 × 3 = 90.

## Q139
**Pergunta:** prazo do job: 15 dias uteis a partir de 09/11/2026, so seg-sex, sem feriado, nao conta o dia 09/11, conta a partir do proximo util
**Resposta esperada:** 30/11/2026
**Conta:** regra: úteis = segunda a sexta, **sem feriado** (o 20/11/2026, sexta, **entra na conta** porque o enunciado exclui feriado). 09/11/2026 = segunda (não conta) → 1º dia = 10/11/2026 (terça). 10–13 (4), 16–20 (5; inclui 20/11), 23–27 (5) = 14; resta 1: 30/11/2026 (segunda). Conferência por código.

## Q140
**Pergunta:** 3 jobs esse mes: 450 + 1.200 + 680, quanto faturo no total
**Resposta esperada:** 2.330
**Conta:** 450 + 1.200 = 1.650; 1.650 + 680 = 2.330.

---

## Resumo lote 3
- Contagem: **Q121–Q140 = 20** (todas calculáveis com dados na frase; soma geral Q01–Q140 = 140)
- Distribuição: casa 5 (Q121–Q125), carro 5 (Q126–Q130), viagem 5 (Q131–Q135), trabalho freela 5 (Q136–Q140)
- Também cobrem usos reais das ferramentas mais usadas: juros (Q124 compostos, Q138 simples), troco (Q122), conversões (Q123 caixas/m², Q128 mm→cm, Q132 câmbio do enunciado), datas (Q125, Q133, Q139)
- Datas conferidas por código; Q125 e Q139 usam regra **sem feriado** (declarada). Q139 conta 20/11/2026 de propósito, por essa regra.
- Nenhuma pergunta do lote 3 repete o enunciado dos lotes 1 e 2.
