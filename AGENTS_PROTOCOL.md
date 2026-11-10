> 🚨 **RUMO NOVO (2026-11-09): leia [RUMO.md](RUMO.md) PRIMEIRO, ele manda mais que este arquivo.**
> Calculadora nova está PAUSADA. Cada agente tem uma FILA no RUMO.md e um painel: rode `python painel.py`
> antes e depois de cada tarefa. Terminou? Pega a próxima da fila na hora. Nunca fique parado esperando.

# 🤖 MANUAL DE INTEGRAÇÃO MULTI-AGENTES — CAIXA DE FERRAMENTAS DO CAIO

> **Público-alvo:** Qualquer agente de Inteligência Artificial (Claude, Cursor, Windsurf, Codex, Gemini, Antigravity, Kilo, Copilot, etc.) operando no ambiente Windows do Caio.
> **Missão:** Expandir a Caixa de Ferramentas rumo à meta de **1 Milhão de Funções / Ferramentas**, trabalhando em paralelo sem quebrar o build nem colidir nomes.

---

## 📒 0. O CATÁLOGO É LEI — consulte ANTES de inventar

A lista oficial de **todas** as ferramentas que já existem fica em **`CATALOGO.md`**, gerada
automaticamente do código por **`catalogo.py`** (nunca edite o `.md` à mão — ele é regerado).

**Fluxo obrigatório de todo agente, toda vez, antes de criar:**

```powershell
Set-Location C:\Users\caion\caixa-ferramentas
# 1) Já existe algo parecido? (evita repetir ferramenta)
C:/Python313/python.exe catalogo.py --check "o que eu vou criar"
# 2) Qual prefixo de 3-4 letras está livre?
C:/Python313/python.exe catalogo.py --prefixos
```

- Se o `--check` disser **⚠️ PROVAVELMENTE JÁ EXISTE**, pare e escolha outra ideia (ou melhore a
  existente, se o Caio pedir). Não crie duplicata.
- Depois de registrar a ferramenta nova (BUILTIN + TOOLS), rode **`python catalogo.py`** pra ela
  entrar no catálogo. Assim a próxima rodada já a enxerga e ninguém repete.

> O catálogo é a **única** fonte confiável de "o que já existe". O BACKLOG é só roteiro de ideias.

---

## 0.1 QUALIDADE MINIMA (regra do Caio, 08/11/2026)
- PROIBIDO criar ferramenta que seja so uma lista fixa de modelos de texto (padrao `PRESETS: dict[str, str]` + render + salvar). Ja existem 77 assim; nao entram mais.
- PROIBIDO gerar ferramentas em serie por script (ex.: `_gen_nxt.py`).
- Toda ferramenta nova precisa: (1) campos de entrada que mudam o resultado; (2) resolver um problema do dia a dia de uma pessoa comum (casa, financas, saude, estudo, trabalho); (3) core com logica real e testes com valores conhecidos.
- O integrador (`fiscal-fabrica\integra.py`) rejeita automaticamente entregas fora dessa regra.

## 0.2 AJUDA OBRIGATORIA (regra do Caio, 09/11/2026)
- Todo `ENTREGA.json` de ferramenta nova DEVE trazer um objeto `"ajuda"` com 4 campos, em portugues simples, escritos a partir da GUI/core REAL (nao invente funcao que nao existe):
  ```json
  "ajuda": {
    "sinopse": "O que a ferramenta faz, em 1-2 frases.",
    "para_que": "Pra quem/quando serve (seja honesto: 'Ferramenta de programador', 'Para estudantes de fisica'...).",
    "como_usar": ["Passo 1 com o nome real do campo/botao", "Passo 2", "Passo 3"],
    "exemplo": "Um caso concreto com numeros/resultado."
  }
  ```
- `como_usar` = lista de 3 a 6 passos curtos, citando os rotulos reais dos campos e botoes.
- O integrador copia esse objeto para `caixa-ferramentas\AJUDA.json` (aparece no botao "?" e no menu "Como usar" de cada card). Sem `"ajuda"` a entrega ainda entra, mas gera AVISO e o card fica so com a descricao curta.

## 🏛️ 1. Arquitetura Fundamental

1. **A Raiz do Projeto:**
   - A central da Caixa fica em: `C:\Users\caion\caixa-ferramentas`.
   - **NUNCA** crie ferramentas dentro de `caixa-ferramentas\`.
   - Todas as ferramentas novas devem ser criadas como **pastas irmãs** em: `C:\Users\caion\<nome-da-ferramenta>`.

2. **O Canivete Suíço está CONGELADO:**
   - O `canivete` possui 800 calculadoras e fica **100% congelado**.
   - Cada nova função/ferramenta solicitada deve ser um **app independente** com seu próprio cartão na interface principal da Caixa.

3. **Estrutura Obrigatória de Cada Ferramenta:**
   Cada pasta de ferramenta (`C:\Users\caion\<nome-da-ferramenta>`) deve conter exatamente 3 arquivos principais com um **PREFIXO EXCLUSIVO de 3 letras** (ex.: `xyz_`):
   - `xyz_core.py` : Motor com a lógica pura, algoritmos, cálculos ou chamadas de sistema (sem UI).
   - `xyz_gui.pyw` : Interface gráfica em PyQt6 completa e responsiva.
   - `test_xyz.py` : Testes automatizados unitários da lógica e smoke test offscreen da interface gráfica.

---

## ⚡ 2. A Regra do Prefixo Único (Prevenção de Colisão)

Durante a compilação, o script `build_suite.py` copia todos os arquivos `.py` e `.pyw` de todas as ferramentas para a pasta temporária `C:\Users\caion\caixa-ferramentas\staged\`.
**SE DOIS ARQUIVOS TIVEREM O MESMO NOME (ex.: dois `core.py` ou dois `test_app.py`), O BUILD É ABORTADO COM ERRO DE COLISÃO!**

### 📋 Prefixos já utilizados (NÃO REPETIR):

**Não decore uma tabela — ela desatualiza.** Peça a lista ao vivo, sempre certa:

```powershell
C:/Python313/python.exe catalogo.py --prefixos
# ou confira um específico junto com a busca de duplicata:
C:/Python313/python.exe catalogo.py --check "minha ideia" -p xyz
```

> 💡 **Instrução para novos agentes:** rode o comando acima e escolha um prefixo inédito de 3 ou 4
> letras que **não** apareça na lista. O `-p xyz` já diz na hora se está livre ou ocupado.

---

## 🖥️ 3. O Padrão Obrigatório da Interface Gráfica (`<px>_gui.pyw`)

1. **Uso de PyQt6** (não PySide6):
   - Imports: `from PyQt6.QtWidgets import ...`, `from PyQt6.QtCore import Qt`, `from PyQt6.QtGui import ...`.
   - Constantes de enum no PyQt6 usam escopo completo: `Qt.AlignmentFlag.AlignCenter`, `Qt.PenStyle.DashLine`, `QHeaderView.ResizeMode.Stretch`.
2. **Tema Visual Escuro Padrão:**
   - Fundo escuro: `#11131a`
   - Painéis e cards: `#171a24` com borda `#262c3d`
   - Destaque/Acento: `#7c5cff` (ou verde `#6ee7b7` / dourado `#ffd166`)
3. **Ponto de Entrada `def main()` OBRIGATÓRIO:**
   Toda GUI **tem que** terminar com esta estrutura, caso contrário a ferramenta não abre dentro do `Caixa.exe`:
   ```python
   def main():
       app = QApplication.instance() or QApplication(sys.argv)
       app.setStyleSheet(QSS)
       w = MinhaJanela()
       w.show()
       sys.exit(app.exec())

   if __name__ == "__main__":
       main()
   ```

---

## 📝 4. Como Registrar a Ferramenta na Caixa

Para a ferramenta aparecer na Caixa e ser compilada no `.exe`, adicione-a em dois arquivos:

1. **Em `C:\Users\caion\caixa-ferramentas\caixa.pyw` (na lista `BUILTIN`):**
   ```python
   ("EMOJI", "Nome da Ferramenta", "Descrição curta de uma frase", "pasta-da-ferramenta", "px_gui.pyw"),
   ```

2. **Em `C:\Users\caion\caixa-ferramentas\build_suite.py` (no dicionário `TOOLS`):**
   ```python
   "pasta-da-ferramenta": "px_gui.pyw",
   ```

---

## ✅ 5. Ciclo de Teste e Compilação (Pipeline)

Antes de considerar uma rodada pronta, execute no PowerShell:

```powershell
# 1. Executar os testes automatizados da sua ferramenta:
$env:PYTHONIOENCODING="utf-8"; $env:QT_QPA_PLATFORM="offscreen"; C:/Python313/python.exe C:\Users\caion\<sua-ferramenta>\test_<px>.py

# 2. Testar se o empacotamento detectou alguma colisão de nome ou import quebrado:
Set-Location C:\Users\caion\caixa-ferramentas
C:/Python313/python.exe build_suite.py --stage-only
C:/Python313/python.exe staged\app.py --selftest

# 3. Compilar o executável final e copiar para a pasta de programas:
Stop-Process -Name "Caixa" -Force -ErrorAction SilentlyContinue
C:/Python313/python.exe build_suite.py
Copy-Item -Path "dist\Caixa\*" -Destination "C:\Users\caion\AppData\Local\Programs\CaixaFerramentas" -Recurse -Force
```

---

## 🚫 6. Regras de Ouro Inegociáveis (Diretrizes do Caio)

- **ZERO PLACEHOLDERS:** Não deixe botões com "em breve", mensagens de `TODO`, ou códigos falsificados que fingem cálculo. Tudo deve funcionar de verdade com dados reais ou algoritmos matemáticos/científicos precisos.
- **INTERNET E SISTEMA SÃO LIVRES:** Se a ferramenta for melhor com internet (APIs abertas, cotações, scraping JSON-LD, NCBI, WHOIS, DNS) ou comandos administrativos locais do Windows (`netsh`, `sc.exe`, `schtasks`, `arp`), sinta-se 100% livre para implementar.
- **SEM SUBAGENTES:** Faça a criação de arquivos de forma direta no disco.
