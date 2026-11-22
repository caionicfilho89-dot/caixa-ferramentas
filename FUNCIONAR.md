# 🔧 FAZER FUNCIONAR — revisão de TODAS as ferramentas (pedido do Caio, 17/11/2026)

> "nao era pra eliminar, era pra fazer funcionar" · "faz os agentes arrumarem o app todo"

O Caio abriu ferramentas e achou botão que não faz nada e resultado **falso** (exemplo inventado mostrado
como se fosse real). A partir de agora vale pra TODAS as 769, sem exceção:

## A regra

1. **A função principal tem que funcionar de verdade** no PC do Caio (Windows 11, sem placa Wi-Fi, só cabo,
   sem scanner, com Spotify/Edge). Use os dados reais do Windows/arquivo/entrada do usuário.
2. **Nunca mostre resultado inventado como se fosse real.** Se o PC não tem o recurso (placa Wi-Fi, scanner,
   bateria, câmera, internet), a ferramenta DIZ isso claramente e o que fazer ("Este PC não tem placa Wi-Fi…").
3. **Exemplo só quando o usuário pede**, por um botão escrito "Exemplo"/"Carregar exemplo", e a tela avisa
   "🧪 DEMONSTRAÇÃO — dados fictícios". NÃO apague o exemplo que já existe: deixe ele atrás do botão.
   (Calculadora/editor que abre com valores de partida editáveis pode continuar assim — o ruim é exemplo que
   *finge* ser resultado real de algo do PC.)
4. **Todo botão faz o que diz.** Clicou e nada aconteceu = defeito. Clicou e deu erro = defeito.
5. **Abre sem cair no `pythonw`/exe.** Erro dentro de `paintEvent`/timer/botão derruba o app inteiro
   (PyQt6) — sem console você nem vê o erro. Por isso o `pyflakes` tem que dar zero "undefined name".
6. **Nunca mude a ferramenta pra agradar o robô.** Proibido: desligar/esconder botão quando `CAIXA_TESTE=1`
   (o portão recusa), trocar comportamento que o Caio usa (ex.: menu que abria no clique) ou piorar a
   segurança (ex.: trocar `os.replace` por escrita direta — aconteceu no lote 2 e foi desfeito). Se o robô
   está errado, avise o Claude pelo correio. O robô já aciona cada item de botão com menu e já permite
   apagar/mover/renomear dentro da pasta temporária dele.

## Passo a passo por ferramenta (C:/Users/caion/<pasta>)

1. Leia o `.pyw` e o `_core.py`. Ache: exemplo/demo/simulação carregado sozinho (no `__init__`, no `except`,
   ou quando "não achou nada"), `random` no lugar de medição, botão ligado a função vazia/`pass`/TODO.
2. Conserte a função REAL. Se depende de hardware/permissão que pode faltar, detecte e explique na tela.
3. Rode e deixe tudo verde:
   ```
   python -m pyflakes <arquivos .py/.pyw da pasta>            # zero "undefined name"
   python C:/Users/caion/caixa-ferramentas/robo_botoes.py <pasta> <script.pyw>   # "erros": []
   python test_<px>.py                                          # testes da pasta
   ```
   O `robo_botoes.py` abre a ferramenta fora da tela e clica em TODOS os botões com segurança (nada é
   apagado/rodado de verdade) — a última linha é um JSON com `"erros"`. Tem que ser `[]`.
4. Abra de verdade por uns segundos: `pythonw <script>.pyw` (tem que continuar aberto) e use a função
   principal com um dado real.
5. Acrescente um teste da função real em `test_<px>.py` quando consertar algo.

## Ao concluir o lote

`python painel.py <você> --concluir T## "C:/Users/caion/<pasta1>: <o que consertou>; robo 0 erros, pyflakes 0, testes OK; C:/Users/caion/<pasta2>: ..."`

- Cite **todas** as pastas do lote (`C:/Users/caion/<pasta>`), uma por uma — mesmo as que já estavam boas
  ("já funcionava: testei X com Y").
- O **portão** roda, em **todas as pastas do lote** (citadas ou não): os testes, o `pyflakes`, o
  `robo_botoes.py` e a busca de botão desligado em modo de teste. Qualquer erro → a tarefa volta pra você
  com o motivo.
- Não mexa em `staged/` nem `dist/`. Não apague exemplo: esconda atrás do botão.
