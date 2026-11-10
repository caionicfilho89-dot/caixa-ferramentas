# PERGUNTAS.md — 60 casos de teste no estilo do Caio (gabarito à mão)
Autor: Grok Bot (crítico/testador) · revisão 2026-11-09 20:35

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
