# COBERTURA.md

Gerado pelo Grok Build em 2026-11-10.
Fonte: `catalogo.montar()` (a lista `BUILTIN` de `caixa.pyw`) e as chaves citadas em `adp_*.py`.
Nao edite a mao se for regerar: o numero muda quando entra adaptador novo.

## Resumo

- Ferramentas no catalogo: **750**.
- Com pelo menos um adaptador na barra: **253**.
- Sem adaptador: **497**.
- Registros de frase (uma chave pode ter mais de um): **348**.

## Adaptadores por arquivo

| Arquivo | Chaves |
|---|---:|
| `adp_arquivos.py` | 17 |
| `adp_audio.py` | 10 |
| `adp_casa.py` | 35 |
| `adp_ciencia.py` | 37 |
| `adp_dev.py` | 28 |
| `adp_essenciais.py` | 16 |
| `adp_financas.py` | 22 |
| `adp_imagem.py` | 19 |
| `adp_jogos.py` | 14 |
| `adp_outras.py` | 25 |
| `adp_rede.py` | 15 |
| `adp_texto.py` | 15 |
| `adp_unidades.py` | 6 |

## Sem adaptador, por categoria

| Categoria | Sem adaptador |
|---|---:|
| 🧰 Outras | 175 |
| 🏠 Casa, Pet & Pessoal | 88 |
| 💰 Finanças & Trabalho | 66 |
| 💻 Dev & Dados | 54 |
| 🗂️ Arquivos & Sistema | 41 |
| 🌐 Rede & Segurança | 32 |
| 🖼️ Imagem & Design | 20 |
| 🎵 Áudio & Vídeo | 11 |
| ✍️ Texto & Estudo | 5 |
| 🔬 Ciência & Engenharia | 3 |
| 🎮 Jogos & Diversão | 2 |

## 15 destaques do Grok (F2)

| Chave | Na barra |
|---|---|
| `faxina-disco` | nao. Varre o disco. O sensor da Hoje ja mostra o C:. |
| `organizador-downloads` | nao. Varre a pasta Downloads. O sensor da Hoje ja conta os arquivos. |
| `print-anotador` | nao. Abre um print. O sensor da Hoje ja lista as capturas. |
| `area-transferencia` | nao. Le a area de transferencia ao vivo. O sensor da Hoje ja mostra. |
| `controle-garantias` | nao. Cadastro em arquivo. O sensor de vencimentos ja avisa. |
| `controle-validade-remedios` | nao. Cadastro em arquivo. O sensor de vencimentos ja avisa. |
| `controle-assinaturas` | sim |
| `info-pc` | sim |
| `calculadora-troco` | sim |
| `calculadora-ipva` | sim |
| `calculadora-rendimento-tinta` | sim |
| `dias-uteis-pagamento` | sim |
| `financas` | sim |
| `kit-pdf` | nao. Precisa de um PDF. A barra nao abre arquivo. |
| `calculadora-botijao-gas` | nao. A frase do botijao ja cai em botijao-gas. Outra chave com as mesmas palavras duplicaria a carta. |

## adp_outras.py (esta leva)

26 frases, 25 chaves. Cada uma com 3 jeitos de perguntar no `test_adp_outras.py`.
De fora, de proposito: gerador de arquivo, inspetor, checklist, o que so varre disco e cadastro sem conta.

- `autonomia-caixa-dagua` — Autonomia Caixa d Agua
- `calculadora-ar-condicionado` — Dimensionador de Ar-Condicionado
- `calculadora-caucao` — Caução de Aluguel
- `calculadora-dsr-hora-extra` — DSR sobre Horas Extras
- `calculadora-energia-eolica-aerogerador` — Energia Eólica, Aerogeradores & Limite de Betz
- `calculadora-engrenagens` — Calculadora de Engrenagens
- `calculadora-indice-conforto` — Índice de Conforto Térmico
- `calculadora-iptu` — Estimativa de IPTU
- `calculadora-simples-nacional` — Simples Nacional e MEI
- `cashback-real` — Cashback Real
- `cisterna-chuva` — Cisterna de Água de Chuva
- `consumo-energia` — Consumo de Energia da Casa
- `cubagem-cargas` — Cubagem & Cargas 3D
- `custo-pedagio-tag` — Pedágio × TAG
- `custo-total-por-km` — Custo Total por km
- `diluicao-limpeza` — Diluição Limpeza
- `dizimo-doacoes` — Dízimo e Doações
- `estimativa-frete` — Estimativa de Frete
- `estudio-gray-code` — Código de Gray
- `meta-poupanca-viagem` — Meta Poupança Viagem
- `numero-extenso` — Números por Extenso & Romanos
- `pensao-alimenticia` — Pensão Alimentícia
- `reajuste-aluguel` — Reajuste de Aluguel
- `saldo-prestacoes` — Saldo de Prestacoes
- `teoria-filas` — Teoria das Filas

## Chaves sem adaptador

### 🧰 Outras

- `relogio-mundial` — Relógio Mundial
- `volume-apps` — Volume por App
- `gerador-senhas` — Gerador de Senhas
- `ficha-medica` — Prontuário & Exames
- `arvore-decisao` — Árvore de Decisão & ID3
- `calculadora-obra` — Calculadora de Obra
- `otimizador-mochila` — Otimizador da Mochila
- `estudio-bezier` — Estúdio Bézier
- `token-bucket` — Token Bucket
- `calculadora-tensao-cisalhamento-mohr` — Círculo de Mohr & Tensões 2D
- `calculadora-equacoes-estado-gases` — Equações de Estado & Gases Reais
- `mala-viagem` — Mala de Viagem
- `marmitas-semana` — Marmitas da Semana
- `placar-truco` — Placar de Truco
- `simulador-precessao-giroscopica` — Simulador Precessao Giroscopica
- `simulador-renda-fixa` — Simulador de Renda Fixa
- `visualizador-ordenacao` — Visualizador de Ordenação
- `simulador-epidemias` — Simulador de Epidemias
- `gerador-escalas-trabalho` — Gerador de Escalas de Trabalho
- `carta-psicrometrica` — Carta Psicrométrica
- `cinematica-robotica` — Cinemática Robótica
- `calculadora-aerodinamica-arrasto-sustentacao` — Aerodinâmica, Sustentação & Arrasto
- `calculadora-vazao-placa-orificio` — Vazão em Placa de Orifício (ISO 5167)
- `despensa-validade` — Despensa e Validades
- `guia-lavanderia` — Guia de Lavanderia
- `pelada-futebol` — Organizador de Pelada
- `plano-concurso` — Plano de Estudos para Concurso
- `rodizio-carona` — Rodízio de Carona
- `treino-academia` — Treino de Academia
- `desafio-poupanca` — Desafio da Poupança
- `vinhos-queijos` — Harmonização de Vinhos e Queijos
- `reologia-fluidos` — Reologia de Fluidos Não Newtonianos
- `tunelamento-quantico` — Simulador de Tunelamento Quântico 1D
- `casa-segura-bebe` — Casa Segura para o Bebê
- `chas-presentes` — Chá de Bebê, Panela e Casa Nova
- `placar-domino` — Placar de Dominó
- `aniversarios-familia` — Aniversários da Família
- `calibragem-pneus` — Calibragem e Rodízio de Pneus
- `contador-linhas-codigo` — Contador de Linhas de Código
- `aluguel-quartos` — Divisão de Aluguel por Quarto
- `cartela-anticoncepcional` — Cartela do Anticoncepcional
- `chimarrao-terere` — Chimarrão e Tererê
- `gerador-license` — Gerador de LICENSE
- `vencimento-documentos` — Vencimento de Documentos
- `analisador-todo` — Analisador de TODO/FIXME
- `comparador-semver` — Comparador SemVer
- `emprestimos-objetos` — Empréstimos de Objetos
- `cinetica-decaimento-nuclear-bateman` — Cinética de Decaimento Nuclear e Bateman
- `detector-caminhos-longos` — Caminhos Longos
- `engrenagens-planetarias-epicicloidais` — Simulador de Engrenagens Planetárias e Epicicloidais
- `gerador-bandit-yaml` — Gerador de .bandit
- `gerador-bunfig` — Gerador bunfig.toml
- `gerador-cargo-toml` — Gerador Cargo.toml
- `gerador-clang-format` — Gerador de .clang-format
- `gerador-clang-tidy` — Gerador .clang-tidy
- `gerador-cmakelists` — Gerador CMakeLists
- `gerador-commitizen` — Gerador Commitizen
- `gerador-flake8` — Gerador de .flake8
- `gerador-isort-cfg` — Gerador de .isort.cfg
- `gerador-meson` — Gerador meson.build
- `gerador-mypy-ini` — Gerador de mypy.ini
- `gerador-nvmrc` — Gerador de .nvmrc
- `gerador-poetry-pyproject` — Gerador Poetry
- `gerador-pylint` — Gerador de .pylintrc
- `gerador-pytest-ini` — Gerador de pytest.ini
- `gerador-ruff-toml` — Gerador de ruff.toml
- `gerador-setup-cfg` — Gerador de setup.cfg
- `gerador-syncthingignore` — Gerador .stignore
- `gerador-tox-ini` — Gerador de tox.ini
- `gerador-yarnrc` — Gerador .yarnrc.yml
- `limpeza-pycache` — Limpeza de __pycache__
- `gerador-procfile` — Gerador Procfile
- `gerador-tool-versions` — Gerador .tool-versions
- `gerador-envrc` — Gerador .envrc
- `gerador-brewfile` — Gerador Brewfile
- `gerador-clangd` — Gerador .clangd
- `gerador-yamllint` — Gerador .yamllint
- `gerador-hadolint` — Gerador .hadolint.yaml
- `gerador-noxfile` — Gerador noxfile.py
- `gerador-winget` — Gerador manifesto Winget
- `gerador-invoke` — Gerador tasks.py (Invoke)
- `gerador-pip-conf` — Gerador pip.conf
- `gerador-condarc` — Gerador .condarc
- `gerador-nsis` — Gerador script NSIS
- `gerador-inno-setup` — Gerador script Inno Setup
- `gerador-bazel` — Gerador Bazel MODULE/BUILD
- `gerador-wix` — Gerador WiX
- `gerador-gemspec` — Gerador gemspec
- `gerador-thrift` — Gerador Thrift IDL
- `gerador-asyncapi` — Gerador AsyncAPI
- `gerador-raml` — Gerador RAML
- `gerador-smithy` — Gerador Smithy
- `gerador-flatbuffers` — Gerador FlatBuffers
- `analisador-yarn-lock` — Analisador yarn.lock
- `gerador-dhall` — Gerador Dhall
- `gerador-flake-nix` — Gerador flake.nix
- `gerador-helm-chart` — Gerador Helm Chart
- `gerador-terraform` — Gerador Terraform
- `gerador-ansible` — Gerador Ansible
- `simulador-campo-magnetico-biot-savart` — Simulador de Campo Magnético & Biot-Savart
- `calculadora-hidratacao-treino` — Calculadora de Hidratação & Reposição de Eletrólitos
- `controle-garantias` — Controle de Garantias
- `controle-validade-cosmeticos` — Validade de Cosmeticos
- `controle-validade-remedios` — Controle de Validade de Remedios
- `quitador-dividas-bola-neve` — Quitador Bola de Neve
- `rateio-condominio-m2` — Rateio Condominio por m2
- `calculadora-reserva-emergencia` — Calculadora & Planejador da Reserva de Emergência
- `estimativa-seguro-residencial` — Seguro Residencial
- `hospedagem-vs-aluguel` — Hospedagem × Aluguel
- `rendimento-pao-caseiro` — Rendimento Pão Caseiro
- `rendimento-sabao-caseiro` — Sabão Caseiro
- `academia-vs-equipamentos` — Academia × Equipamentos
- `comparador-planos-internet` — Planos de Internet
- `custo-escola-particular` — Custo Escola Particular
- `distribuicao-refeicoes-macros` — Distribuição de Calorias e Macros por Refeição
- `lavanderia-vs-maquina` — Lavanderia × Máquina
- `prestacao-vs-aluguel` — Prestação × Aluguel
- `streaming-vs-cinema` — Streaming × Cinema
- `academia-infantil` — Academia Infantil
- `arroz-feijao-porcao` — Arroz & Feijão
- `custo-creche` — Custo Creche
- `custo-oculos` — Custo de Óculos
- `desconto-progressivo` — Desconto Progressivo
- `diluicao-alvejante` — Diluição Alvejante
- `diluicao-amaciante` — Diluição Amaciante
- `estacionamento-mensalista` — Estacionamento Mensalista
- `fermento-natural` — Fermento Natural
- `gasolina-postos` — Gasolina Postos
- `lavagem-a-seco` — Lavagem a Seco × Casa
- `manicure-spa-vs-casa` — Manicure Salão × Casa
- `plano-celular-gb` — Planos de Celular
- `seguro-auto-franquia` — Seguro Auto × Franquia
- `uber-vs-onibus` — Uber × Ônibus
- `validade-produtos-limpeza` — Validade Limpeza
- `calculadora-seguro-desemprego` — Calculadora de Seguro-Desemprego
- `custo-home-office` — Custo Home Office vs Escritorio
- `custo-jardineiro` — Custo Jardineiro
- `ingresso-cinema-3d` — Cinema 2D × 3D
- `ingresso-show` — Ingresso Show
- `madeira-reforma` — Madeira p/ Reforma
- `indice-massa-muscular` — Índice de Massa Muscular (FFMI)
- `analisador-volume-treino-semanal` — Analisador de Volume de Treino Semanal (Hipertrofia)
- `calculadora-densidade-estudo-pomodoro` — Calculadora de Densidade de Estudo & Foco Cognitivo
- `cargas-power-bank` — Cargas do Power Bank
- `custo-consulta-especialista` — Custo Consulta Especialista
- `indice-qualidade-sono-psqi` — Índice de Qualidade do Sono (PSQI simplificado)
- `prazos-direito-consumidor` — Prazos do Consumidor
- `analisador-perfil-lipidico-cardiovascular` — Analisador de Perfil Lipídico & Risco Aterogênico (SBC)
- `calculadora-contribuicao-sindical` — Contribuicao Sindical & Assistencial
- `calculadora-custo-estagiario-empresa` — Calculadora de Custo de Estagiário para Empresas (Lei 11.788)
- `consertar-ou-trocar-celular` — Consertar ou Trocar o Celular
- `controle-agua-diaria-copos` — Controle de Agua Diaria por Copos
- `frete-gratis-vale-a-pena` — Frete Grátis Vale a Pena?
- `indice-estresse-percebido` — Índice de Estresse Percebido (simplificado)
- `multa-transito-pontos` — Multa de Trânsito e Pontos
- `hora-de-sair` — Hora de Sair
- `planejador-intervalo-almoco` — Planejador de Intervalo de Almoco
- `planejador-meta-redacao` — Planejador de Meta de Redacao
- `terra-para-vasos` — Terra para Vasos
- `controle-hidratacao-escritorio` — Controle de Hidratação no Escritório
- `indice-burnout-simplificado` — Indice simplificado de burnout
- `agua-mineral-vs-filtro` — Água Mineral × Filtro
- `carga-semanal-risco-burnout` — Carga Semanal e Risco de Burnout
- `checklist-prova-certificacao` — Checklist Prova de Certificação
- `comparador-plano-odonto` — Plano Odontológico × Particular
- `estimativa-hba1c-glicemias` — Estimativa HbA1c & eAG
- `estimativa-vo2max-cooper` — Estimativa VO2máx Cooper
- `gas-encanado-vs-botijao` — Gás Encanado × Botijão
- `indice-equilibrio-vida-trabalho` — Índice Equilíbrio Vida-Trabalho
- `indice-fadiga-turno` — Índice de Fadiga de Turno
- `mapa-gap-habilidades` — Mapa de Gap de Habilidades
- `mensalidade-escola-vs-bolsa` — Mensalidade Escola × Bolsa
- `multa-cancelamento-academia` — Multa Cancelamento Academia
- `saque-aniversario-fgts` — Saque-Aniversário FGTS
- `seguro-viagem-cobertura` — Seguro Viagem × Cobertura

### 🏠 Casa, Pet & Pessoal

- `tarefas` — Tarefas
- `calendario-br` — Calendário BR
- `contatos` — Contatos
- `leitor-ebooks` — Leitor de E-books
- `receitas` — Receitas
- `controle-carro` — Controle do Carro
- `habitos` — Hábitos
- `canivete` — Canivete Suíço
- `inspetor-executavel` — Inspetor de Executáveis
- `cofre-snippets` — Cofre de Snippets
- `inspetor-http` — Receptor de Webhooks
- `estudio-rotas` — Estúdio de Rotas GPX
- `agendador-tarefas` — Simulador Cron & Agendador
- `horta-jardim` — Horta & Adubação NPK
- `inspetor-processos` — Inspetor de Processos
- `inspetor-pcap` — Inspetor de Pacotes PCAP
- `flashcards-repeticao` — Flashcards com Repetição Espaçada
- `inspetor-unicode` — Inspetor Unicode
- `calculadora-motores-eletricos` — Calculadora de Motores Elétricos
- `calculadora-acustica-salas` — Calculadora de Acústica de Salas
- `fatoracao-primos` — Fatoração de Primos
- `diario-criptografado` — Diário Criptografado
- `calculadora-hidroponia` — Calculadora de Hidroponia
- `inspetor-ads` — Inspetor de Streams ADS
- `planejador-mudanca` — Planejador de Mudança
- `analisador-difracao-raios-x-bragg` — Difração de Raios-X (Bragg)
- `inspetor-acl` — Inspetor ACL NTFS
- `inspetor-pem` — Inspetor PEM / Certificados
- `rega-plantas` — Rega de Plantas
- `tarefas-casa` — Tarefas da Casa e Mesada
- `carro-ou-app` — Carro Próprio ou Aplicativo
- `limpa-temp` — Limpa Temp
- `rotina-skincare` — Rotina de Skincare
- `sabonetes-velas` — Sabonetes e Velas Artesanais
- `diario-pressao` — Diário de Pressão e Glicemia
- `manutencao-casa` — Manutenção da Casa
- `calendario-safra` — Calendário de Safra
- `calorias-receita` — Calorias da Receita
- `cafe-da-manha` — Cardápio de Café da Manhã
- `dinamica-veicular-pacejka` — Dinâmica Veicular & Pneu de Pacejka
- `inspetor-shebang` — Inspetor de Shebang
- `sono-bebe` — Diário de Sono do Bebê
- `troca-oleo` — Troca de Óleo do Carro
- `vacinas-pet` — Carteira de Vacinas do Pet
- `banco-horas` — Banco de Horas
- `escala-plantao` — Escala de Plantão
- `diario-pesca` — Diário de Pesca
- `analisador-tamanho-funcoes` — Tamanho de Funcoes
- `gerador-black` — Gerador Black
- `gerador-setuptools-scm` — Gerador setuptools_scm
- `inspetor-dll-exports` — Inspetor de Exports DLL
- `inspetor-elf` — Inspetor ELF
- `inspetor-zip-central` — Inspetor ZIP
- `inspetor-macho` — Inspetor Mach-O
- `inspetor-pe-imports` — Inspetor PE Imports
- `inspetor-pe-version` — Inspetor PE Version Info
- `inspetor-wheel` — Inspetor de Wheel
- `inspetor-dist-info` — Inspetor dist-info / egg-info
- `inspetor-cargo-lock` — Inspetor Cargo.lock
- `inspetor-go-sum` — Inspetor go.sum
- `calculadora-propriedades-secao-inercia` — Calculadora de Propriedades de Seção & Inércia
- `calculadora-botijao-gas` — Calculadora de Botijao de Gas
- `estimativa-conta-agua` — Estimativa de Conta de Agua
- `calculadora-meia-vida-cafeina` — Calculadora de Meia-Vida da Cafeína & Sono
- `planejador-ciclo-ebbinghaus` — Planejador da Curva de Ebbinghaus & Revisões
- `entrada-carro-seminovo` — Entrada Carro Seminovo
- `planejador-revisao-provas` — Planejador de Revisão para Provas
- `planejador-sessao-foco` — Planejador de Sessão de Foco
- `calculadora-densidade-calorica-saciedade` — Calculadora de Densidade Calórica & Saciedade
- `adaptacao-jet-lag` — Adaptação ao Jet Lag
- `checklist-entrevista-emprego` — Checklist de Preparacao para Entrevista
- `comparador-hospedagens` — Comparador de Hospedagens
- `controle-medicacao-horarios` — Agenda de Medicacao por Horarios
- `indice-produtividade-pessoal` — Indice de Produtividade Pessoal
- `organizador-tarefas-eisenhower` — Matriz Eisenhower
- `calendario-da-horta` — Calendário da Horta
- `checklist-saida-emprego` — Checklist de Saida do Emprego
- `controle-cafeina-doses-dia` — Controle de Doses de Cafeína no Dia
- `checklist-primeira-semana-estagio` — Checklist 1a Semana de Estagio
- `caixa-leitner-intervalos` — Caixa de Leitner (Intervalos)
- `calculadora-dosagem-medicamento-pediatrico` — Calculadora de Dosagem Pediátrica por Peso Corporal
- `calculadora-dosagem-suplementacao-esportiva` — Calculadora de Dosagem de Suplementação Esportiva (ISSN)
- `calculadora-tempo-recuperacao-muscular` — Calculadora de Tempo de Recuperação Muscular & Supercompensação
- `custo-deslocamento-trabalho` — Custo de Deslocamento ao Trabalho
- `meta-revisoes-anki-diarias` — Meta de Revisões Anki
- `planejador-recuperacao-pos-treino` — Recuperação Pós-Treino
- `planejador-soneca-poder` — Planejador de Soneca Poder
- `roteiro-entrevista-star` — Roteiro Entrevista STAR

### 💰 Finanças & Trabalho

- `extrator-texto` — Extrator de Texto
- `pix-boleto` — Pix & Boleto
- `orcamentos` — Orçamentos e Recibos
- `curriculo-pdf` — Currículo em PDF
- `controle-gastos` — Controle de Gastos
- `price-monitor` — Monitor de Preços
- `calculadora-gorjeta` — Gorjeta e Divisão
- `teste-hardware` — Teste de Periféricos
- `leitor-nfe` — Leitor de NF-e XML
- `gerador-ofx` — Gerador de Extratos OFX
- `calculadora-estatistica-bayesiana` — Estatística & Inferência Bayesiana
- `codigo-resistores` — Código de Cores de Resistores
- `calculadora-banda` — Calculadora de Banda & Armazenamento
- `rf-calculo` — Calculadora RF & dBm
- `validador-formato-cartao-credito` — Validador de Cartão de Crédito
- `bingo-familia` — Bingo em Família
- `comparador-mercado` — Comparador de Preços do Mercado
- `extrator-icones` — Extrator de Icones
- `planejador-casamento` — Planejador de Casamento
- `calculadora-impressao-3d` — Calculadora de Impressão 3D
- `orcamento-natal` — Orçamento de Natal
- `rateio-condominio` — Rateio de Condomínio
- `chocolate-pascoa` — Chocolate e Ovos de Páscoa
- `orcamento-reforma` — Orçamento de Reforma
- `conta-luz-republica` — Rateio da Conta de Luz
- `calorias-atividade` — Calorias da Atividade
- `frete-vendas` — Frete e Embalagem para Vender Online
- `extrator-strings-binario` — Extrator de Strings Binario
- `gerador-manpage` — Gerador de man page
- `calculadora-deficit-calorico` — Calculadora de Déficit Calórico, TDEE & Macros
- `calculadora-taxa-delivery` — Taxa e Gorjeta Delivery
- `reserva-emergencia` — Reserva de Emergencia
- `comparador-atacado-varejo` — Atacado × Varejo
- `custo-empregado-domestico` — Custo Empregado Doméstico
- `cartucho-vs-toner` — Cartucho × Toner
- `comparador-generico-marca` — Genérico × Marca
- `diluicao-agua-sanitaria` — Diluição Água Sanitária
- `entrada-financiamento` — Entrada Financiamento
- `orcamento-festa` — Orçamento de Festa
- `orcamento-mudanca` — Orçamento de Mudança
- `planejador-compras-atacado` — Compras no Atacado
- `simulador-abono-pecuniario-ferias` — Simulador de Abono Pecuniário — Venda de Férias CLT
- `gorjeta-buffet` — Gorjeta Buffet
- `lista-feira-orcamento` — Lista da Feira
- `orcamento-lua-de-mel` — Orçamento Lua de Mel
- `simulador-financiamento-estudantil-fies` — Simulador do Novo FIES & Amortização
- `simulador-plr` — Simulador de PLR
- `taxa-pix-recebimento` — Taxa Pix Recebimento
- `carga-horaria-creditos` — Carga Horária & Créditos
- `imposto-compra-internacional` — Imposto de Compra Internacional
- `simulador-banco-horas-compensacao` — Simulador de Banco de Horas & Compensação (CLT)
- `calculadora-beneficio-vr-va` — Calculadora VR/VA Mensal
- `indice-satisfacao-trabalho` — Índice de Satisfação no Trabalho
- `calculadora-adicional-periculosidade` — Adicional de Periculosidade CLT
- `calculadora-adicional-noturno` — Calculadora Adicional Noturno
- `calculadora-equiparacao-salarial-clt` — Calculadora de Equiparação Salarial & Reflexos Trabalhistas (Art. 461 CLT)
- `calculadora-taxa-metabolica-katch-mcardle` — Calculadora de Taxa Metabólica & TDEE (Katch-McArdle)
- `calculadora-zonas-frequencia-cardiaca-karvonen` — Calculadora de Zonas de Frequência Cardíaca (Karvonen & HRR)
- `consignado-vs-credito-pessoal` — Consignado × Crédito Pessoal
- `custo-fralda-geriatrica` — Custo Fralda Geriátrica
- `frete-sedex-vs-pac` — Frete Sedex × PAC
- `lance-consorcio` — Lance de Consórcio
- `orcamento-manutencao-predial` — Orçamento Manutenção Predial
- `orcamento-presentes-casamento` — Orçamento Presentes de Casamento
- `orcamento-reforma-cozinha` — Orçamento Reforma de Cozinha
- `simulador-transicao-carreira-reserva` — Simulador de Transição de Carreira & Runway Financeiro

### 💻 Dev & Dados

- `calculadora-cientifica` — Calculadora Científica
- `visualizador-planilhas` — Visualizador de Planilhas
- `cliente-api` — Cliente de API
- `visualizador-sqlite` — Visualizador SQLite
- `caderno-python` — Caderno Python
- `treino-digitacao` — Treino de Digitação
- `estudio-markdown` — Estúdio Markdown & TeX
- `estudio-cronometro` — Cronômetro & Relógio Xadrez
- `gerador-sitemap` — Gerador de Sitemap & Robots
- `gerador-diagramas-sequence` — Gerador de Diagramas de Sequência
- `gerador-graficos` — Gerador de Gráficos
- `gerador-gitignore` — Gerador de .gitignore
- `jogo-stop` — Jogo Stop (Adedonha)
- `gerador-gitattributes` — Gerador de .gitattributes
- `gerador-makefile` — Gerador de Makefile
- `gerador-tree` — Gerador de Tree
- `gerador-dockerignore` — Gerador de .dockerignore
- `gerador-requirements` — Gerador de requirements.txt
- `gerador-pre-commit` — Gerador de pre-commit
- `gerador-badges` — Gerador de Badges
- `analisador-funcoes-duplicadas` — Funcoes Duplicadas
- `analisador-imports-nao-usados` — Imports Nao Usados
- `arvore-diretorios` — Arvore de Diretorios
- `gerador-codeowners` — Gerador CODEOWNERS
- `gerador-coveragerc` — Gerador de .coveragerc
- `gerador-eslintignore` — Gerador de .eslintignore
- `gerador-github-actions` — Gerador de GitHub Actions
- `gerador-prettierrc` — Gerador de .prettierrc
- `gerador-justfile` — Gerador justfile
- `gerador-taskfile` — Gerador Taskfile.yml
- `gerador-vagrantfile` — Gerador Vagrantfile
- `gerador-python-version` — Gerador .python-version
- `gerador-earthfile` — Gerador Earthfile
- `gerador-pyrightconfig` — Gerador pyrightconfig.json
- `gerador-dependabot` — Gerador Dependabot
- `gerador-renovate` — Gerador Renovate
- `gerador-markdownlint` — Gerador .markdownlint
- `gerador-vscode-launch` — Gerador VS Code launch.json
- `gerador-sqlfluff` — Gerador .sqlfluff
- `gerador-goreleaser` — Gerador .goreleaser
- `gerador-devcontainer` — Gerador Dev Container
- `gerador-vscode-tasks` — Gerador VS Code tasks.json
- `gerador-scoop` — Gerador manifesto Scoop
- `gerador-mise` — Gerador mise.toml
- `gerador-appxmanifest` — Gerador AppxManifest
- `gerador-lldbinit` — Gerador .lldbinit
- `gerador-cyclonedx` — Gerador CycloneDX SBOM
- `gerador-avro` — Gerador schema Avro
- `gerador-graphql` — Gerador GraphQL SDL
- `gerador-cue` — Gerador CUE
- `gerador-kustomization` — Gerador Kustomization
- `gerador-pulumi` — Gerador Pulumi
- `cronograma-do-evento` — Cronograma do Evento
- `checklist-prova-oral-banca` — Checklist Prova Oral / Banca

### 🗂️ Arquivos & Sistema

- `faxina-disco` — Faxina de Disco
- `recupera-arquivos` — Recupera Arquivos
- `busca-arquivos` — Busca de Arquivos
- `renomeador` — Renomeador em Lote
- `area-transferencia` — Área de Transferência
- `rastreador-tempo` — Rastreador de Tempo
- `tempo` — Tempo
- `monitor-sistema` — Monitor do Sistema
- `inicializacao` — Inicialização
- `compactador` — Compactador
- `janelas` — Janelas
- `comparar-pastas` — Comparar Pastas
- `variaveis-ambiente` — Variáveis de Ambiente
- `site-blocker` — Bloqueador de Sites
- `duplicate-detector` — Detector de Duplicatas
- `disk-analyzer` — Analisador de Espaço
- `gerenciador-servicos` — Gerenciador de Serviços
- `benchmark-pc` — Benchmark de Memória & SSD
- `analisador-cpu-termico` — Analisador de CPU & Topologia
- `links-ntfs` — Links NTFS & Atalhos
- `diff-hex` — Diff Hex Binario
- `monitor-pasta` — Monitor de Pasta
- `quem-trava-arquivo` — Quem Trava o Arquivo
- `analisador-path` — Analisador de PATH
- `calculadora-posicao-solar-astronomia` — Posição Solar & Algoritmo SPA
- `editor-hosts-linhas` — Editor de Hosts por Linhas
- `introducao-alimentar` — Introdução Alimentar do Bebê
- `lixeira-windows` — Lixeira do Windows
- `comparador-timestamps` — Comparador de Timestamps
- `arquivos-recentes` — Arquivos Recentes
- `detector-symlinks-quebrados` — Symlinks Quebrados
- `listador-hardlinks` — Listador de Hardlinks
- `localizador-arquivos-vazios` — Localizador de Arquivos Vazios
- `top-arquivos-grandes` — Top Arquivos Grandes
- `gerador-nmake` — Gerador Makefile nmake
- `gerador-protobuf` — Gerador Protobuf
- `gerador-grpc` — Gerador gRPC service
- `roi-curso-certificacao` — ROI de Curso & Certificação Profissional
- `checklist-onboarding-emprego` — Checklist de Onboarding no Novo Emprego
- `rastreador-deep-work-semanal` — Deep Work Semanal
- `rotina-mobilidade-lombar` — Rotina Mobilidade Lombar

### 🌐 Rede & Segurança

- `cofre-senhas` — Cofre de Senhas
- `cripto-arquivos` — Trancar Arquivos
- `rede` — Rede
- `organizador-downloads` — Organizador de Downloads
- `cabecalhos-seguranca` — Boas Práticas do Site
- `autenticador-2fa` — Autenticador 2FA
- `notas-criptografadas` — Notas Criptografadas
- `compartilhar-rede` — Compartilhar na Rede
- `mapa-mental` — Mapa Mental
- `auditoria-pc` — Auditoria de Portas
- `analisador-wifi` — Analisador de Wi-Fi
- `auditor-seo` — Auditor de SEO & Links
- `scanner-rede` — Scanner de Rede Local
- `analisador-logs` — Analisador de Logs SIEM
- `gerenciador-firewall` — Gerenciador de Firewall
- `gerador-ssh` — Chaves SSH & Config
- `gerador-ssl` — Gerador de Certificados SSL
- `estudio-criptografia-curvas-elipticas` — Estúdio Criptografia Curvas Elípticas
- `calculadora-redes-neurais-mlp` — Estúdio de Redes Neurais MLP
- `detector-magic` — Detector Magic / MIME
- `gerador-editorconfig` — Gerador de .editorconfig
- `scanner-segredos` — Scanner de Segredos
- `gerador-changelog` — Gerador de CHANGELOG
- `gerador-npmignore` — Gerador de .npmignore
- `analisador-package-lock` — Analisador de package-lock
- `analisador-pip-freeze` — Analisador pip freeze
- `gerador-npmrc` — Gerador de .npmrc
- `listador-deps-pe` — Listador de Dependencias PE
- `gerador-chocolatey-nuspec` — Gerador Chocolatey nuspec
- `gerador-openapi` — Gerador OpenAPI
- `analisador-pnpm-lock` — Analisador pnpm-lock.yaml
- `comparador-proposta-estagio` — Comparador de Propostas de Estagio

### 🖼️ Imagem & Design

- `kit-pdf` — Kit de PDF
- `qrcode-tool` — QR Code
- `print-anotador` — Print Anotador
- `conversor-imagens` — Conversor de Imagens
- `capturador-cores` — Capturador de Cores
- `editor-imagem` — Editor de Imagem
- `paletas` — Paletas de Cores
- `webcam` — Webcam
- `fontes` — Visualizador de Fontes
- `galeria-fotos` — Galeria de Fotos
- `etiquetas` — Etiquetas
- `quadro-branco` — Quadro Branco
- `scanner-documentos` — Scanner de Documentos
- `quadro-kanban` — Quadro Kanban
- `estudios-gif` — Estúdio de GIF & Sprites
- `corte-chapas` — Corte de Chapas 2D
- `estudio-svg` — Estúdio Vetorial SVG
- `quadro-branco-colaborativo` — Quadro Branco Colaborativo
- `detector-newline-final` — Newline final
- `gerador-gdbinit` — Gerador .gdbinit

### 🎵 Áudio & Vídeo

- `gravador-tela` — Gravador de Tela
- `conversor-av` — Conversor Áudio/Vídeo
- `gravador-voz` — Gravador de Voz
- `player-musica` — Player de Música
- `editor-legendas` — Editor de Legendas
- `laboratorio-audio` — Laboratório de Áudio
- `gravador-macros` — Automação & Macros
- `estudio-midi` — Estúdio Piano Roll & MIDI
- `estudio-som` — Estúdio de Áudio & Ondas
- `analisador-audio-fft` — Analisador de Áudio & FFT
- `material-escolar` — Material Escolar

### ✍️ Texto & Estudo

- `ferramentas-br` — Ferramentas BR
- `notas-md` — Notas
- `texto-fala` — Texto para Fala
- `leitor-rss` — Leitor de Feeds RSS
- `detector-encoding-misto` — Encoding Misto

### 🔬 Ciência & Engenharia

- `estudio-grafos` — Estúdio de Grafos & Dijkstra
- `simulador-gravitacional-n-corpos` — Simulador Gravitacional N-Corpos
- `analisador-imports-circulares` — Imports Circulares

### 🎮 Jogos & Diversão

- `limpa-metadados` — Limpar Metadados
- `dummy-data-generator` — Gerador de Dados
