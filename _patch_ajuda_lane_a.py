# -*- coding: utf-8 -*-
"""Injeta objeto ajuda em ENTREGA.json das ferramentas Lane A (Cursor)."""
from __future__ import annotations
import json, re
from pathlib import Path

BASE = Path(r"C:\Users\caion")

# pasta -> ajuda (sinopse, para_que, como_usar, exemplo) — alinhado à GUI real
AJUDAS = {
"calculadora-ipva": {
  "sinopse": "Calcula o IPVA a partir do valor venal, aliquota da UF e numero de cotas.",
  "para_que": "Para quem vai pagar IPVA do carro/moto e quer simular cotas e aliquota.",
  "como_usar": [
    "Informe o Valor venal do veiculo.",
    "Ajuste a Aliquota (%) tipica da sua UF.",
    "Escolha o tipo (auto/moto) se houver e o numero de Cotas.",
    "Clique em Calcular e leia o valor total e por cota."
  ],
  "exemplo": "Venal R$ 50.000, aliquota 3%, 3 cotas → cerca de R$ 1.500 no ano (~R$ 500/cota)."
},
"calculadora-botijao-gas": {
  "sinopse": "Compara preco do botijao e estima dias de autonomia pelo consumo.",
  "para_que": "Para quem cozinha a gas e quer saber rendimento e melhor preco.",
  "como_usar": [
    "Informe o Preco do botijao e o peso em kg.",
    "Ajuste o Consumo diario estimado.",
    "Clique em Calcular para ver dias de autonomia e custo/dia."
  ],
  "exemplo": "Botijao 13 kg a R$ 120 com 0,4 kg/dia → ~32 dias e ~R$ 3,75/dia."
},
"calculadora-troco": {
  "sinopse": "Calcula o troco e decompõe em notas e moedas.",
  "para_que": "Para caixa de loja, feira ou quem precisa fechar o troco rapidinho.",
  "como_usar": [
    "Digite o Total da compra.",
    "Digite o Valor pago.",
    "Clique em Calcular e veja o troco e as cedulas/moedas."
  ],
  "exemplo": "Total R$ 37,50 pago com R$ 50 → troco R$ 12,50."
},
"controle-validade-remedios": {
  "sinopse": "Lista remedios com validade e alerta os que vencem em breve.",
  "para_que": "Para farmacinha de casa e quem controla estoque de remedios.",
  "como_usar": [
    "Cadastre o nome e a Data de validade do remedio.",
    "Use o botao de adicionar/listar conforme a tela.",
    "Veja os alertas de itens proximos do vencimento."
  ],
  "exemplo": "Remedio com validade em 15 dias aparece em alerta; vencido fica destacado."
},
"estimativa-conta-agua": {
  "sinopse": "Estima a conta de agua pelo consumo em m3 e tarifa.",
  "para_que": "Para quem quer prever a conta antes da leitura da companhia.",
  "como_usar": [
    "Informe o Consumo em m3.",
    "Ajuste a Tarifa e taxas extras se houver.",
    "Clique em Calcular para ver o valor estimado."
  ],
  "exemplo": "12 m3 a R$ 8/m3 → cerca de R$ 96 (mais taxas se informadas)."
},
"calculadora-rendimento-tinta": {
  "sinopse": "Calcula quantos litros/latas de tinta para a area, com demaos e perda.",
  "para_que": "Para reforma e pintura residencial.",
  "como_usar": [
    "Informe a Area em m2 e o Rendimento (m2/L).",
    "Ajuste Demaos e Perda %.",
    "Clique em Calcular para ver litros e latas."
  ],
  "exemplo": "40 m2, 10 m2/L, 2 demaos, 10% perda → cerca de 8,8 L."
},
"comparador-avista-parcelado": {
  "sinopse": "Compara compra a vista (com desconto) versus parcelado com juros.",
  "para_que": "Para decidir se vale a vista ou no cartao/crediario.",
  "como_usar": [
    "Informe o Preco a vista e o desconto, se houver.",
    "Informe Parcelas, valor da parcela ou taxa.",
    "Clique em Comparar e veja qual sai mais barato."
  ],
  "exemplo": "R$ 1.000 a vista vs 10x R$ 110 → parcelado custa R$ 1.100."
},
"controle-garantias": {
  "sinopse": "Registra garantias de produtos e avisa quando estao acabando.",
  "para_que": "Para organizar garantia de eletrodomesticos e eletronicos.",
  "como_usar": [
    "Cadastre o produto e a Data fim da garantia.",
    "Consulte a lista e os alertas de vencimento.",
    "Atualize quando renovar ou encerrar."
  ],
  "exemplo": "TV com garantia ate 2027-06-01; faltando 60 dias gera alerta."
},
"saldo-prestacoes": {
  "sinopse": "Mostra quanto ja pagou e quanto falta de um financiamento/crediario.",
  "para_que": "Para acompanhar saldo devedor de prestacoes.",
  "como_usar": [
    "Informe o Valor total e o Numero de parcelas.",
    "Informe quantas Parcelas ja pagas.",
    "Clique em Calcular para ver pago, restante e saldo."
  ],
  "exemplo": "12x de R$ 200, 5 pagas → pago R$ 1.000, faltam R$ 1.400."
},
"calculadora-estacionamento": {
  "sinopse": "Calcula o custo do estacionamento por tempo (fracao/hora/diaria).",
  "para_que": "Para quem deixa o carro em estacionamento por horas ou diaria.",
  "como_usar": [
    "Informe o Tempo de permanencia.",
    "Ajuste a Tabela de precos (hora/fracao).",
    "Clique em Calcular."
  ],
  "exemplo": "3 horas a R$ 12/hora → R$ 36."
},
"rateio-condominio-m2": {
  "sinopse": "Rateia o condominio pelo metro quadrado de cada unidade.",
  "para_que": "Para sindicos e moradores conferirem o rateio por area.",
  "como_usar": [
    "Informe o Valor total e a Area total.",
    "Informe a Area da sua unidade.",
    "Clique em Calcular para ver sua parte."
  ],
  "exemplo": "Total R$ 10.000, predio 1.000 m2, apto 80 m2 → R$ 800."
},
"reserva-emergencia": {
  "sinopse": "Calcula a reserva de emergencia em meses de gasto e o aporte mensal.",
  "para_que": "Para planejamento financeiro pessoal de colchao de seguranca.",
  "como_usar": [
    "Informe o Gasto mensal e os Meses desejados de reserva.",
    "Informe quanto ja tem guardado.",
    "Clique em Calcular para ver a meta e o aporte."
  ],
  "exemplo": "Gasto R$ 4.000, meta 6 meses, ja tem R$ 5.000 → falta R$ 19.000."
},
"calculadora-taxa-delivery": {
  "sinopse": "Soma subtotal, taxa de entrega, gorjeta e desconta cupom.",
  "para_que": "Para fechar o total real do pedido de delivery.",
  "como_usar": [
    "Preencha Subtotal, Taxa de entrega e Gorjeta % ou fixa.",
    "Informe Cupom se houver.",
    "Clique em Calcular."
  ],
  "exemplo": "Subtotal R$ 100 + taxa R$ 10 + gorjeta 10% → R$ 120."
},
"controle-validade-cosmeticos": {
  "sinopse": "Controla PAO (validade apos abertura) de cosmeticos.",
  "para_que": "Para quem usa cremes/maquiagem e nao quer produto vencido.",
  "como_usar": [
    "Informe a Data de abertura e os Meses de PAO.",
    "Clique em Calcular para ver a validade e o status."
  ],
  "exemplo": "Aberto em 01/01 com PAO 12 meses → validade ~01/01 do ano seguinte."
},
"quitador-dividas-bola-neve": {
  "sinopse": "Ordena dividas no metodo bola de neve e estima quitacao.",
  "para_que": "Para quem quer quitar varias dividas com estrategia.",
  "como_usar": [
    "Liste as dividas (saldo e parcela minima).",
    "Informe o valor extra mensal disponivel.",
    "Clique em Calcular a ordem e o tempo."
  ],
  "exemplo": "Dividas de R$ 500 e R$ 2.000: quita a menor primeiro e joga o valor na maior."
},
"comparador-preco-unitario": {
  "sinopse": "Compara preco por unidade/kg/ml entre embalagens.",
  "para_que": "Para compras no mercado e escolher o melhor custo-beneficio.",
  "como_usar": [
    "Informe Preco e Quantidade do produto A e do B.",
    "Clique em Comparar.",
    "Veja qual tem menor preco unitario."
  ],
  "exemplo": "R$ 10 / 500 g vs R$ 18 / 1 kg → o de 1 kg sai R$ 0,018/g."
},
"dias-uteis-pagamento": {
  "sinopse": "Conta dias uteis entre datas, com feriados nacionais.",
  "para_que": "Para vencimentos, folha e prazos de pagamento.",
  "como_usar": [
    "Informe a Data inicial e a Data final.",
    "Marque se inclui feriados.",
    "Clique em Calcular."
  ],
  "exemplo": "Segunda a sexta da mesma semana → 5 dias uteis."
},
"autonomia-caixa-dagua": {
  "sinopse": "Estima dias de autonomia da caixa d'agua pelo consumo.",
  "para_que": "Para casas com caixa e risco de falta de agua.",
  "como_usar": [
    "Informe a Capacidade em litros e o Consumo diario.",
    "Clique em Calcular para ver os dias de autonomia."
  ],
  "exemplo": "Caixa 1000 L, consumo 200 L/dia → 5 dias."
},
"calculadora-iptu": {
  "sinopse": "Estima IPTU pelo valor venal, aliquota, desconto e parcelas.",
  "para_que": "Para proprietarios que querem simular o IPTU da prefeitura.",
  "como_usar": [
    "Preencha Valor venal e Aliquota.",
    "Informe Desconto (cota unica etc.) e Parcelas.",
    "Clique em Calcular."
  ],
  "exemplo": "Venal R$ 200.000, 1%, desconto 10%, 1 parcela → R$ 1.800."
},
"rendimento-pao-caseiro": {
  "sinopse": "Estima quantos paes saem da fornada e o custo por pao.",
  "para_que": "Para quem assa pao em casa e controla custo.",
  "como_usar": [
    "Informe Farinha (g), Custo da farinha e Outros custos.",
    "Ajuste Peso alvo do pao e Perda no forno.",
    "Clique em Calcular."
  ],
  "exemplo": "500 g farinha, perda 12%, pao 400 g → 1 pao; custo conforme insumos."
},
"hospedagem-vs-aluguel": {
  "sinopse": "Compara um mes de hospedagem (diaria) com aluguel + custos.",
  "para_que": "Para quem esta em duvida entre Airbnb/hotel e alugar.",
  "como_usar": [
    "Preencha Diaria, Dias no mes e Taxas/limpeza.",
    "Preencha Aluguel, Condominio e Contas.",
    "Clique em Comparar."
  ],
  "exemplo": "Diaria R$ 180 x 30 + limpeza R$ 150 vs aluguel R$ 2.200 + custos → mostra o mais barato."
},
"estimativa-seguro-residencial": {
  "sinopse": "Estima premio anual de seguro residencial sobre imovel + conteudo.",
  "para_que": "Para ter uma ordem de grandeza antes da cotacao real.",
  "como_usar": [
    "Informe Valor do imovel e Conteudo.",
    "Ajuste Taxa anual, Franquia e Desconto.",
    "Clique em Estimar."
  ],
  "exemplo": "R$ 400 mil + R$ 80 mil a 0,15% a.a. → premio ~R$ 720/ano."
},
"decimo-terceiro-proporcional": {
  "sinopse": "Calcula 13o proporcional CLT menos adiantamento.",
  "para_que": "Para empregados CLT conferirem o 13o do holerite.",
  "como_usar": [
    "Informe Salario bruto e Meses trabalhados.",
    "Informe Adiantamento ja pago, se houver.",
    "Clique em Calcular."
  ],
  "exemplo": "Salario R$ 3.000, 6 meses, adiantamento R$ 600 → a receber R$ 600."
},
"custo-total-por-km": {
  "sinopse": "Calcula R$/km somando combustivel e fixos diluidos (IPVA, seguro etc.).",
  "para_que": "Para motoristas que querem o custo real por quilometro.",
  "como_usar": [
    "Informe Preco do litro, Consumo e Km no mes.",
    "Preencha IPVA, Seguro, Manutencao e Estacionamento.",
    "Clique em Calcular."
  ],
  "exemplo": "R$ 6/L, 10 km/L, 1000 km, sem fixos → R$ 0,60/km."
},
"controle-assinaturas": {
  "sinopse": "Soma assinaturas convertendo ciclos (mensal/anual etc.) para total mensal e anual.",
  "para_que": "Para quem quer enxergar o gasto real com streaming, apps e academias.",
  "como_usar": [
    "Preencha Nome, Valor e Ciclo e clique em Adicionar.",
    "Ou cole linhas no campo de lista (nome;valor;ciclo).",
    "Clique em Somar para ver Total mensal e Total anual.",
    "Use Remover selecionada para tirar um item da lista."
  ],
  "exemplo": "Netflix R$ 55,90 mensal + Adobe R$ 714 anual → ~R$ 115,40/mes."
},
"comparador-atacado-varejo": {
  "sinopse": "Compara preco unitario de atacado vs varejo, com desperdicio opcional.",
  "para_que": "Para compras no atacado sem se enganar com embalagem grande.",
  "como_usar": [
    "Informe Preco e Qtd. do varejo e do atacado.",
    "Ajuste Desperdicio estimado se parte pode estragar.",
    "Clique em Comparar."
  ],
  "exemplo": "Varejo R$ 10/1 un vs atacado R$ 48/6 un → atacado a R$ 8/un."
},
"custo-empregado-domestico": {
  "sinopse": "Estima custo mensal do empregador com salario, VT e encargos eSocial.",
  "para_que": "Para familias que contratam empregado domestico.",
  "como_usar": [
    "Informe Salario, Vale-transporte e Outros beneficios.",
    "Marque ou desmarque Incluir FGTS rescisório.",
    "Clique em Calcular."
  ],
  "exemplo": "Salario R$ 1.000 + encargos tipicos → cerca de R$ 1.200/mes (com rescisório)."
},
"rendimento-sabao-caseiro": {
  "sinopse": "Calcula usos, custo por ml/uso e economia vs produto comercial.",
  "para_que": "Para quem faz sabao/detergente caseiro.",
  "como_usar": [
    "Informe Litros produzidos e Custo dos insumos.",
    "Ajuste ml por uso e Preco comercial.",
    "Clique em Calcular."
  ],
  "exemplo": "5 L a R$ 25, 50 ml/uso → 100 usos a R$ 0,25/uso."
},
"reajuste-plano-saude": {
  "sinopse": "Projeta a mensalidade do plano de saude com reajuste composto.",
  "para_que": "Para familias planejarem o impacto do reajuste anual.",
  "como_usar": [
    "Informe Mensalidade atual e Reajuste anual %.",
    "Escolha Anos a frente e Beneficiarios.",
    "Clique em Projetar."
  ],
  "exemplo": "R$ 100 com 10% a.a. por 2 anos → R$ 121/mes."
},
"estimativa-frete": {
  "sinopse": "Heuristica de frete por peso, distancia e modalidade.",
  "para_que": "Para ter uma estimativa educativa antes da cotacao oficial.",
  "como_usar": [
    "Informe Peso e Distancia.",
    "Escolha a Modalidade (economico/expresso/mesmo_dia).",
    "Opcional: Valor declarado e Taxa de seguro.",
    "Clique em Estimar."
  ],
  "exemplo": "2 kg, 200 km, economico → frete base cerca de R$ 27."
},
"calculadora-caucao": {
  "sinopse": "Calcula deposito/caucao de aluguel e o custo de oportunidade se investido.",
  "para_que": "Para inquilinos e proprietarios discutirem a caucao.",
  "como_usar": [
    "Informe Aluguel mensal e Meses de caucao.",
    "Ajuste Duracao do contrato e Rendimento estimado.",
    "Clique em Calcular."
  ],
  "exemplo": "Aluguel R$ 2.000, 3 meses de caucao → deposito R$ 6.000."
},
"lavanderia-vs-maquina": {
  "sinopse": "Compara custo mensal da lavanderia com lavar em casa.",
  "para_que": "Para decidir se vale a pena lavar fora ou em casa.",
  "como_usar": [
    "Informe Cargas/mes e Preco lavanderia/carga.",
    "Preencha kWh, tarifas, sabao e Depreciacao.",
    "Clique em Comparar."
  ],
  "exemplo": "12 cargas a R$ 35 na lavanderia vs ~R$ 3–5/carga em casa + depreciacao."
},
"meta-poupanca-viagem": {
  "sinopse": "Calcula quanto guardar por mes para bater a meta da viagem.",
  "para_que": "Para quem esta juntando para viajar com prazo definido.",
  "como_usar": [
    "Informe Meta da viagem e Meses ate a viagem.",
    "Preencha Ja guardado e Rendimento mensal.",
    "Clique em Calcular."
  ],
  "exemplo": "Meta R$ 8.000, 10 meses, R$ 500 ja guardados → aporte mensal calculado."
},
"comparador-planos-internet": {
  "sinopse": "Compara planos de internet por R$/Mbps, com fidelidade e multa.",
  "para_que": "Para escolher o plano de fibra/banda larga com melhor custo por Mbps.",
  "como_usar": [
    "Preencha Nome, Preco, Mbps, Fidelidade e Multa e clique em Adicionar plano.",
    "Ou cole linhas no campo de lista (nome;preco;Mbps;fidelidade;multa).",
    "Clique em Comparar para ver o Melhor custo/Mbps.",
    "Use Remover selecionado para ajustar a lista."
  ],
  "exemplo": "Plano R$ 120 / 400 Mbps (R$ 0,30/Mbps) vence um de R$ 100 / 100 Mbps."
},
"diluicao-limpeza": {
  "sinopse": "Dilui produto concentrado (C1·V1=C2·V2) para o volume final.",
  "para_que": "Para limpeza domestica com produtos concentrados.",
  "como_usar": [
    "Informe Concentracao do produto e Concentracao desejada.",
    "Informe Volume final em ml.",
    "Clique em Calcular para ver ml de produto e de agua."
  ],
  "exemplo": "100% → 5% em 1000 ml → 50 ml de produto + 950 ml de agua."
},
"orcamento-festa": {
  "sinopse": "Orca festa/aniversario por adultos, criancas, comida, bebida e fixos.",
  "para_que": "Para quem esta planejando festa e precisa do total e por pessoa.",
  "como_usar": [
    "Informe Adultos e Criancas.",
    "Preencha custos de comida, bebida, decoracao, bolo, local e Outros.",
    "Ajuste Taxa de servico e clique em Calcular."
  ],
  "exemplo": "10 adultos, comida R$ 40 + bebida R$ 20 + fixos, com 10% de taxa → total na tela."
},
"academia-vs-equipamentos": {
  "sinopse": "Compara mensalidade da academia com comprar equipamentos em casa.",
  "para_que": "Para decidir entre academia e montar cantinho de treino.",
  "como_usar": [
    "Informe Mensalidade, Meses no horizonte e Custo dos equipamentos.",
    "Ajuste Manutencao e Taxa/matricula.",
    "Clique em Comparar."
  ],
  "exemplo": "R$ 100/mes por 12 meses vs kit R$ 500 → casa mais barata; payback ~5 meses."
},
"custo-escola-particular": {
  "sinopse": "Soma anuidade, material, uniforme, transporte e extras da escola.",
  "para_que": "Para familias com filhos em escola particular.",
  "como_usar": [
    "Informe Mensalidade e Meses cobrados/ano.",
    "Preencha Material, Uniforme, Transporte e Alimentacao.",
    "Clique em Calcular."
  ],
  "exemplo": "Mensalidade R$ 1.800 x 12 + material R$ 800 → media mensal real na tela."
},
"reembolso-plano-saude": {
  "sinopse": "Estima reembolso: min(pago, tabela) x % − coparticipacao, com teto.",
  "para_que": "Para quem usa reembolso de consultas/exames no plano.",
  "como_usar": [
    "Informe Valor pago e Valor tabela.",
    "Ajuste % cobertura, Coparticipacao e Teto.",
    "Clique em Calcular."
  ],
  "exemplo": "Pago R$ 500, tabela R$ 400, 80%, copart R$ 30 → reembolso R$ 290."
},
"pensao-alimenticia": {
  "sinopse": "Estima pensao como % da renda liquida, por filho, com extras.",
  "para_que": "Referencia educativa — valor final e acordo/judicial.",
  "como_usar": [
    "Informe Renda liquida, Percentual e Filhos.",
    "Inclua Outras despesas se quiser.",
    "Clique em Calcular."
  ],
  "exemplo": "Renda R$ 4.000, 30%, 2 filhos → pensao R$ 1.200 (R$ 600/filho)."
},
"cartucho-vs-toner": {
  "sinopse": "Compara custo por pagina de cartucho jato vs toner laser.",
  "para_que": "Para escritorio/casa escolher impressao mais barata.",
  "como_usar": [
    "Informe Preco e Paginas do cartucho e do toner.",
    "Informe Paginas/mes.",
    "Clique em Comparar."
  ],
  "exemplo": "Cartucho R$ 100/200 pag vs toner R$ 300/2000 pag → toner mais barato por pagina."
},
"planejador-compras-atacado": {
  "sinopse": "Define quanto comprar no atacado sem estourar orcamento nem validade.",
  "para_que": "Para compras mensais no atacado com disciplina de estoque.",
  "como_usar": [
    "Informe Consumo semanal, Semanas de estoque e Preco unitario.",
    "Ajuste Orcamento e Validade em dias.",
    "Clique em Planejar."
  ],
  "exemplo": "Consumo 2 un/sem, 4 semanas, R$ 10, orcamento R$ 50 → comprar 5 un."
},
"entrada-financiamento": {
  "sinopse": "Calcula entrada %, saldo financiado e prestacao Price do imovel.",
  "para_que": "Para simular financiamento imobiliario de forma educativa.",
  "como_usar": [
    "Informe Valor do imovel e Entrada %.",
    "Ajuste Taxa anual e Prazo (meses).",
    "Clique em Calcular."
  ],
  "exemplo": "Imovel R$ 100.000, entrada 20%, taxa 0%, 100 meses → parcela R$ 800."
},
"prestacao-vs-aluguel": {
  "sinopse": "Compara custo mensal de comprar (prestacao+encargos) vs alugar.",
  "para_que": "Para a decisao comprar ou alugar no curto prazo.",
  "como_usar": [
    "Preencha Prestacao, Seguro, IPTU e Cond. (compra).",
    "Preencha Aluguel e Cond. (aluguel).",
    "Opcional: Valorizacao e Valor do imovel.",
    "Clique em Comparar."
  ],
  "exemplo": "Prestacao R$ 3.000 vs aluguel R$ 2.000 → aluguel mais barato no mes (sem valorizacao)."
},
"petsitter-vs-creche": {
  "sinopse": "Compara petsitter por hora, creche e hotelzinho no periodo.",
  "para_que": "Para donos de pet em viagem ou expediente longo.",
  "como_usar": [
    "Informe Dias e Horas/dia (sitter).",
    "Preencha precos de Petsitter/hora, Creche/dia e Hotelzinho/dia.",
    "Clique em Comparar."
  ],
  "exemplo": "5 dias, sitter R$ 50/h x 8 h vs creche R$ 80/dia → creche mais barata."
},
"orcamento-mudanca": {
  "sinopse": "Estima mudanca: caminhoes, caixas, ajudantes, km e seguro.",
  "para_que": "Para quem vai mudar de casa e precisa de um total aproximado.",
  "como_usar": [
    "Informe Volume e Capacidade do caminhao.",
    "Preencha precos de caminhao, caixas, ajudantes, km e Seguro.",
    "Clique em Calcular."
  ],
  "exemplo": "30 m3 com caminhao de 15 m3 → 2 caminhoes + frete/embalagem/mao de obra."
},
"cashback-real": {
  "sinopse": "Mostra cashback liquido apos anuidade, IOF e teto.",
  "para_que": "Para avaliar se o cartao com cashback realmente compensa.",
  "como_usar": [
    "Informe Gasto no mes e Cashback anunciado %.",
    "Preencha Anuidade/mes, Teto e IOF.",
    "Clique em Calcular."
  ],
  "exemplo": "Gasto R$ 1.000, 2%, anuidade R$ 10 → liquido R$ 10."
},
"diluicao-agua-sanitaria": {
  "sinopse": "Calcula ml de agua sanitaria para atingir ppm do uso (superficie/roupa/frutas).",
  "para_que": "Para desinfeccao domestica com hipoclorito (educativo).",
  "como_usar": [
    "Informe Teor de cloro e Volume de agua.",
    "Escolha o Uso (superficie, roupa ou frutas).",
    "Clique em Calcular."
  ],
  "exemplo": "2,5% em 1 L para superficie (200 ppm) → 8 ml de sanitaria."
},
"comparador-generico-marca": {
  "sinopse": "Compara preco de remedio de marca vs generico por comprimido.",
  "para_que": "Para farmacia/casa escolher o mesmo principio ativo mais barato.",
  "como_usar": [
    "Informe Preco marca, Preco generico e Comprimidos/caixa.",
    "Clique em Comparar."
  ],
  "exemplo": "Marca R$ 50 vs generico R$ 20 (30 cp) → economia R$ 30 (60%)."
},
"economia-horta-caseira": {
  "sinopse": "Compara valor da colheita ao preco de mercado menos insumos e tempo.",
  "para_que": "Para quem planta em casa e quer ver se economiza de verdade.",
  "como_usar": [
    "Informe kg colhidos/mes e Preco/kg no mercado.",
    "Preencha Insumos, Horas e Valor da hora.",
    "Clique em Calcular."
  ],
  "exemplo": "5 kg a R$ 10/kg, insumos R$ 20 → economia R$ 30."
},
"controle-contas-fixas": {
  "sinopse": "Soma contas fixas mensais e alerta vencimentos proximos.",
  "para_que": "Para organizar o calendario de contas da casa.",
  "como_usar": [
    "Ajuste Alerta (dias).",
    "Liste as contas no formato nome;valor;dia_vencimento.",
    "Clique em Calcular."
  ],
  "exemplo": "Aluguel;2200;5 e Internet;119,90;15 → total mensal e alertas."
},
"entrada-carro-seminovo": {
  "sinopse": "Simula entrada e financiamento Price de carro seminovo com IPVA/seguro/docs.",
  "para_que": "Para quem vai financiar seminovo e quer o custo mensal real.",
  "como_usar": [
    "Informe Valor do carro, Entrada, Taxa anual e Prazo.",
    "Preencha IPVA, Seguro e Docs.",
    "Clique em Calcular."
  ],
  "exemplo": "Carro R$ 50.000, entrada R$ 10.000, taxa 0%, 40x → parcela R$ 1.000."
},
"cafe-casa-vs-cafeteria": {
  "sinopse": "Compara gasto mensal de cafe em casa versus cafeteria.",
  "para_que": "Para viciados em cafe medirem a economia de fazer em casa.",
  "como_usar": [
    "Informe Xicaras/semana e Preco cafeteria.",
    "Preencha Preco do pacote, Xicaras/pacote, Leite e Filtros.",
    "Clique em Comparar."
  ],
  "exemplo": "10 xicaras/semana na cafeteria vs pacote caseiro → casa quase sempre mais barata."
},
"streaming-vs-cinema": {
  "sinopse": "Compara assinaturas de streaming com idas ao cinema no mes.",
  "para_que": "Para decidir se o streaming ainda compensa frente ao cinema.",
  "como_usar": [
    "Informe Streaming/mes, Sessoes/mes, Ingresso, Pipoca e Pessoas.",
    "Clique em Comparar."
  ],
  "exemplo": "Streaming R$ 50 vs 2 sessoes x 2 pessoas (ingresso+pipoca) → streaming mais barato."
},
"desconto-progressivo": {
  "sinopse": "Aplica faixas de desconto progressivo sobre o valor da compra.",
  "para_que": "Para simular promocoes tipo 5% ate X, 10% acima.",
  "como_usar": [
    "Informe Valor da compra.",
    "Liste as faixas (limite;pct), usando inf na ultima.",
    "Clique em Calcular."
  ],
  "exemplo": "R$ 250 com faixas 100;5 / 300;10 / inf;15 → desconto R$ 20."
},
"estacionamento-mensalista": {
  "sinopse": "Compara mensalista com avulso (hora ou diaria).",
  "para_que": "Para quem trabalha fora e escolhe mensalista ou avulso.",
  "como_usar": [
    "Informe Mensalista, Dias no mes, Horas/dia e Precos.",
    "Se Diaria avulsa > 0, ela e usada no lugar da hora.",
    "Clique em Comparar."
  ],
  "exemplo": "Mensalista R$ 300 vs 20 diarias de R$ 25 → mensalista mais barato."
},
"seguro-auto-franquia": {
  "sinopse": "Compara dois seguros pelo custo esperado premio + franquia x sinistros.",
  "para_que": "Para escolher entre premio baixo com franquia alta ou o contrario.",
  "como_usar": [
    "Informe Premio e Franquia dos planos A e B.",
    "Ajuste Sinistros/ano esperados.",
    "Clique em Comparar."
  ],
  "exemplo": "A: premio 3000 franquia 2000; B: 2500/4000; 1 sinistro/ano → A mais barato."
},
"lista-feira-orcamento": {
  "sinopse": "Soma a lista da feira e alerta se estoura o orcamento.",
  "para_que": "Para ir a feira/supermercado com teto de gasto.",
  "como_usar": [
    "Informe o Orcamento.",
    "Liste itens como nome;quantidade;preco.",
    "Clique em Somar."
  ],
  "exemplo": "Banana;2;4,50 + Tomate;1,5;8,90 → total e sobra/estouro."
},
"poupanca-meta": {
  "sinopse": "Projeta saldo com aportes/juros ou calcula meses ate a meta.",
  "para_que": "Para metas financeiras com poupanca ou investimento simples.",
  "como_usar": [
    "Informe Saldo atual, Aporte/mes e Taxa mensal.",
    "Clique em Projetar (com Meses) ou Meses ate meta (com Meta).",
  ],
  "exemplo": "Aporte R$ 100/mes sem juros por 10 meses → R$ 1.000; meta R$ 500 → 5 meses."
},
"taxa-maquininha": {
  "sinopse": "Calcula o liquido apos taxa de debito/credito/parcelado da maquininha.",
  "para_que": "Para MEI e lojistas saberem quanto sobra da venda.",
  "como_usar": [
    "Informe Valor da venda e Taxa a vista.",
    "Ajuste Taxa fixa, Parcelas e Taxa parcelado.",
    "Clique em Calcular."
  ],
  "exemplo": "Venda R$ 100, taxa 2% a vista → voce recebe R$ 98."
},
"custo-curso-idioma": {
  "sinopse": "Soma mensalidade, material, matricula e exame e mostra custo por aula.",
  "para_que": "Para quem vai matricular em curso de idiomas.",
  "como_usar": [
    "Informe Mensalidade, Meses, Material, Matricula e Exame.",
    "Ajuste Aulas/semana.",
    "Clique em Calcular."
  ],
  "exemplo": "R$ 450 x 12 + material R$ 200 → custo total e por aula na tela."
},
"plano-celular-gb": {
  "sinopse": "Compara planos de celular por GB e custo com excedente.",
  "para_que": "Para escolher o plano movel pelo seu consumo real.",
  "como_usar": [
    "Informe Seu consumo em GB.",
    "Liste planos (nome;preco;GB;R$/GB excedente) ou edite a lista.",
    "Clique em Comparar."
  ],
  "exemplo": "Consumo 20 GB: plano 10 GB + excedente pode sair mais caro que um de 40 GB."
},
"fermento-natural": {
  "sinopse": "Calcula escalas de alimentacao do starter (fermento natural).",
  "para_que": "Para panificacao com fermento natural (levain).",
  "como_usar": [
    "Informe Starter atual e Razoes de agua e farinha.",
    "Escolha quantas Alimentacoes.",
    "Clique em Calcular."
  ],
  "exemplo": "50 g starter 1:1:1 → 150 g apos uma alimentacao."
},
"manicure-spa-vs-casa": {
  "sinopse": "Compara manicure no salao com kit + esmaltes em casa.",
  "para_que": "Para decidir entre salao e rotina caseira de unhas.",
  "como_usar": [
    "Informe Preco no salao e Visitas/mes.",
    "Preencha Custo do kit, Duracao e Esmaltes/mes.",
    "Clique em Comparar."
  ],
  "exemplo": "2 visitas x R$ 50 vs kit R$ 100 em 10 meses + R$ 10 esmalte → casa mais barata."
},
"academia-infantil": {
  "sinopse": "Calcula custo de esporte/academia infantil com extras e transporte.",
  "para_que": "Para pais com filhos em atividade esportiva paga.",
  "como_usar": [
    "Informe Mensalidade e Meses.",
    "Preencha Uniforme, Matricula, Competicoes e Transporte.",
    "Clique em Calcular."
  ],
  "exemplo": "Mensalidade R$ 220 x 12 + uniforme R$ 180 → media mensal real na tela."
},
"diluicao-amaciante": {
  "sinopse": "Dilui amaciante concentrado por partes produto:agua.",
  "para_que": "Para render o amaciante concentrado sem errar a proporcao.",
  "como_usar": [
    "Informe Partes produto e Partes agua.",
    "Informe Volume final em ml.",
    "Clique em Calcular."
  ],
  "exemplo": "1:3 em 1000 ml → 250 ml de amaciante + 750 ml de agua."
},
"uber-vs-onibus": {
  "sinopse": "Compara gasto mensal de app (Uber etc.) com transporte publico.",
  "para_que": "Para quem vai e volta do trabalho e quer ver o custo dos dois modos.",
  "como_usar": [
    "Informe Corridas app/mes e Preco medio da corrida.",
    "Informe Passagem, Viagens publico e Vale-transporte.",
    "Clique em Comparar."
  ],
  "exemplo": "10 corridas x R$ 30 vs 40 passagens x R$ 5 → publico mais barato."
},
"taxa-extra-condominio": {
  "sinopse": "Rateia taxa extra de condominio de forma igualitaria ou por fracao ideal.",
  "para_que": "Para obras, fundo e chamadas extras do condominio.",
  "como_usar": [
    "Informe Valor total e Modo (igualitario/fracao).",
    "No igualitario: Unidades e Suas unidades; na fracao: Sua fracao ideal.",
    "Clique em Calcular."
  ],
  "exemplo": "R$ 40.000 / 40 unidades → R$ 1.000 por unidade."
},
"validade-produtos-limpeza": {
  "sinopse": "Calcula validade apos abertura (PAO) de produtos de limpeza.",
  "para_que": "Para nao usar desinfetante/detergente vencido apos aberto.",
  "como_usar": [
    "Escolha Aberto em no calendario.",
    "Informe PAO em meses.",
    "Clique em Calcular."
  ],
  "exemplo": "Aberto ha pouco com PAO 12 meses → status ok e data limite."
},
"custo-creche": {
  "sinopse": "Calcula custo de creche com mensalidade, material, matricula e alimentacao.",
  "para_que": "Para familias com bebe/crianca em creche paga.",
  "como_usar": [
    "Informe Mensalidade e Meses.",
    "Preencha Material, Matricula e Alimentacao/mes.",
    "Clique em Calcular."
  ],
  "exemplo": "R$ 1.800 x 12 + material R$ 300 → total e media mensal na tela."
},
"material-escolar": {
  "sinopse": "Soma a lista de material e compara com o kit da escola.",
  "para_que": "Para a volta as aulas decidir entre kit e compra avulsa.",
  "como_usar": [
    "Informe Kit da escola (0 = so soma).",
    "Liste itens nome;qtd;preco.",
    "Clique em Calcular."
  ],
  "exemplo": "Lista R$ 200 vs kit R$ 350 → comprar avulso mais barato."
},
"lavagem-a-seco": {
  "sinopse": "Compara lavagem a seco com lavar pecas delicadas em casa.",
  "para_que": "Para ternos/vestidos: tinturaria vs produto caseiro.",
  "como_usar": [
    "Informe Pecas/mes e Preco/peca (seco).",
    "Preencha Produto, Depreciacao, Horas e Valor da hora.",
    "Clique em Comparar."
  ],
  "exemplo": "4 pecas x R$ 40 no seco vs R$ 25 de produto em casa → casa mais barata."
},
"custo-oculos": {
  "sinopse": "Soma armacao, lentes, exame, antirreflexo e garantia com desconto.",
  "para_que": "Para orcar oculos novos na otica.",
  "como_usar": [
    "Preencha Armacao, Lentes, Exame, Antirreflexo e Garantia.",
    "Ajuste Desconto %.",
    "Clique em Calcular."
  ],
  "exemplo": "Armacao+lentes R$ 200 com 10% off → a pagar R$ 180."
},
"arroz-feijao-porcao": {
  "sinopse": "Converte arroz/feijao cru em cozido e conta porcoes e custo.",
  "para_que": "Para marmita e planejamento de feira da semana.",
  "como_usar": [
    "Informe Arroz cru e Feijao cru (g).",
    "Ajuste fatores, porcoes e custos.",
    "Clique em Calcular."
  ],
  "exemplo": "300 g arroz + 200 g feijao → varias porcoes; custo por porcao na tela."
},
"gorjeta-buffet": {
  "sinopse": "Calcula total de buffet com couvert, bebidas e gorjeta %.",
  "para_que": "Para fechar a conta do buffet/rodizio em grupo.",
  "como_usar": [
    "Informe Preco buffet/pessoa e Pessoas.",
    "Ajuste Gorjeta, Couvert e Bebidas.",
    "Clique em Calcular."
  ],
  "exemplo": "R$ 100 x 2 pessoas + 10% gorjeta → R$ 220."
},
"hospedagem-pet": {
  "sinopse": "Calcula hotelzinho/creche pet na viagem (diarias x pets + extras).",
  "para_que": "Para donos de pet que viajam e deixam o animal hospedado.",
  "como_usar": [
    "Informe Dias, Diaria/pet e Pets.",
    "Preencha Banho, Transporte e Desconto.",
    "Clique em Calcular."
  ],
  "exemplo": "5 dias x R$ 80 → R$ 400 (1 pet)."
},
"gasolina-postos": {
  "sinopse": "Compara postos incluindo o custo de combustivel do desvio ate la.",
  "para_que": "Para escolher o posto mais barato de verdade, nao so no preco/L.",
  "como_usar": [
    "Informe Litros a encher e Consumo do carro.",
    "Liste postos nome;R$/L;desvio_km.",
    "Clique em Comparar."
  ],
  "exemplo": "Posto mais longe e mais barato pode perder para o da esquina apos o desvio."
},
"diluicao-alvejante": {
  "sinopse": "Calcula ml de alvejante/cloro para atingir ppm na lavagem.",
  "para_que": "Para alvejar roupa com concentracao segura (educativo).",
  "como_usar": [
    "Informe Teor de cloro, Agua na maquina e ppm alvo.",
    "Clique em Calcular."
  ],
  "exemplo": "2,5% em 1 L a 50 ppm → 2 ml de alvejante."
},
"ingresso-cinema-3d": {
  "sinopse": "Compara o custo de sessoes 2D vs 3D com pipoca e pessoas.",
  "para_que": "Para decidir se o 3D vale o extra no mes.",
  "como_usar": [
    "Informe Ingresso 2D, Ingresso 3D, Pessoas, Pipoca e Sessoes/mes.",
    "Clique em Comparar."
  ],
  "exemplo": "2D R$ 30 vs 3D R$ 40, 2 pessoas → extra do 3D R$ 20 na sessao."
},
"taxa-pix-recebimento": {
  "sinopse": "Mostra o liquido ao receber Pix com taxa % e taxa fixa.",
  "para_que": "Para MEI/lojista que recebe Pix via gateway/maquininha.",
  "como_usar": [
    "Informe Valor bruto, Taxa % e Taxa fixa.",
    "Clique em Calcular."
  ],
  "exemplo": "R$ 100 com 1% + R$ 0,50 → liquido R$ 98,50."
},
"orcamento-lua-de-mel": {
  "sinopse": "Orca lua de mel: passagem, hotel, passeios, comida e seguro.",
  "para_que": "Para casais planejando a viagem pos-casamento.",
  "como_usar": [
    "Preencha Passagens, Hotel/noite e Noites.",
    "Informe Passeios, Comida/pessoa/dia, Seguro e Pessoas.",
    "Clique em Calcular."
  ],
  "exemplo": "Passagens R$ 4.000 + 7 noites + comida/passeios → total e por pessoa/dia."
},
"madeira-reforma": {
  "sinopse": "Estima madeira para reforma com perda, frete e mao de obra.",
  "para_que": "Para obras e marcenaria residencial.",
  "como_usar": [
    "Informe Quantidade liquida e Preco/unidade.",
    "Ajuste Perda %, Frete e Mao de obra.",
    "Clique em Calcular."
  ],
  "exemplo": "9 un necessarias com 10% perda → comprar 10 un."
},
"ingresso-show": {
  "sinopse": "Soma ingresso, taxa de servico, transporte, consumo e estacionamento.",
  "para_que": "Para shows e festivais sem surpresa no total.",
  "como_usar": [
    "Informe Ingresso, Pessoas e Taxa servico %.",
    "Preencha Transporte, Consumo e Estacionamento.",
    "Clique em Calcular."
  ],
  "exemplo": "2 ingressos R$ 100 + 10% taxa + R$ 100 extras → R$ 320."
},
"custo-jardineiro": {
  "sinopse": "Compara jardineiro mensal com voce mesmo (horas + insumos).",
  "para_que": "Para donos de quintal/jardim decidirem contratar ou fazer.",
  "como_usar": [
    "Informe Visitas/mes e Preco/visita.",
    "Preencha Suas horas, Valor da hora e Insumos.",
    "Clique em Comparar."
  ],
  "exemplo": "2 visitas x R$ 100 vs 3 h x R$ 20 + R$ 10 insumos → voce mais barato."
},
}

def main():
    ok = skip = miss = 0
    for pasta, ajuda in AJUDAS.items():
        path = BASE / pasta / "ENTREGA.json"
        if not path.exists():
            print("MISS", pasta)
            miss += 1
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        # normaliza como_usar se veio com trailing comma bug
        cu = ajuda["como_usar"]
        if isinstance(cu, str):
            cu = [cu]
        ajuda = dict(ajuda)
        ajuda["como_usar"] = [s for s in cu if s]
        while len(ajuda["como_usar"]) < 3:
            ajuda["como_usar"].append("Confira o resultado na area de saida.")
        assert 3 <= len(ajuda["como_usar"]) <= 6, pasta
        data["ajuda"] = ajuda
        if data.get("status") == "integrado":
            pass  # mantem status
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ok += 1
        print("OK", pasta)
    print(f"done ok={ok} miss={miss}")

if __name__ == "__main__":
    main()
