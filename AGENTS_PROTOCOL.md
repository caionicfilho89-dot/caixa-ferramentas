# 🤖 MANUAL DE INTEGRAÇÃO MULTI-AGENTES — CAIXA DE FERRAMENTAS DO CAIO

> **Público-alvo:** Qualquer agente de Inteligência Artificial (Claude, Cursor, Windsurf, Codex, Gemini, Antigravity, Kilo, Copilot, etc.) operando no ambiente Windows do Caio.
> **Missão:** Expandir a Caixa de Ferramentas rumo à meta de **1 Milhão de Funções / Ferramentas**, trabalhando em paralelo sem quebrar o build nem colidir nomes.

---

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

### 📋 Tabela de Prefixos Já Utilizados (NÃO REPETIR):
```text
kh_  fd_  clt_ cu_  pb_  fa_  cg_  rc_  car_ hb_  sb_  dd_  gd_  as_  pm_
gs_  cm_  nc_  tg_  qb_  cv_  cn_  scn_ lan_ lg_  th_  mm_  kb_  aud_ dk_
gif_ snip_ rss_ svc_ wfi_ seo_ ccp_ dfx_ syn_ mcr_ prx_ ast_ bar_ chm_ crd_
lsc_ elt_ dna_ lga_ gpx_ mtx_ fwl_ dck_ stt_ med_ mid_ sch_ agr_ prc_ svg_
mrs_ cub_ ssk_ nfe_ chz_ ipm_ fsc_ mdx_ ofx_ gsl_ som_ opt_ geo_ bmk_ cmb_
cfr_ tip_ pcp_ crn_ tre_ rgx_ grf_ lgc_ fft_ jsc_ grs_ stm_ nbd_ cnc_ huf_
cll_ gip_ bys_ bnf_ pid_ qth_ crc_ uni_ mtc_ qtn_ phn_ cpt_ bsc_ hdr_ rlc_ sqf_ seq_ bse_
apo_ uid_ wcg_ res_ ext_ crx_ obr_ jwt_ bnd_ pac_ rfc_ jmr_ rpg_ nav_ gst_
blm_ spl_ wci_ knp_ trf_ ecc_ thm_ lhn_ pet_ cab_ rct_
```

> 💡 **Instrução para novos agentes:** Escolha um prefixo inédito de 3 ou 4 letras que não esteja na lista acima.

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
