# 🍔 Estações da Fábrica — divisão de trabalho dos 4 agentes

> **Objetivo:** parar de brigar pelos mesmos arquivos. Hoje os 4 agentes editam `caixa.pyw`,
> `build_suite.py` e os `AGENTS*.md` ao mesmo tempo → conflito constante. Aqui cada um tem uma
> **estação fixa**, como a cozinha do McDonald's: cada um faz a sua parte e no fim sai pronto.
>
> **Regra nº 1 (a mais importante):** **SÓ O INTEGRADOR edita `caixa.pyw`, `build_suite.py` e os
> `AGENTS*.md`.** Os construtores NUNCA tocam nesses arquivos. É isso que elimina os conflitos.

---

## 👥 Quem é quem

| Estação | Agente | O que faz | Toca em arquivos compartilhados? |
|---|---|---|---|
| 🥩 Construtor — Lane A | **Cursor** | Cria ferramentas de **sistema / arquivos / Windows / dev** | ❌ só a pasta dele |
| 🔬 Construtor — Lane B | **Antigravity** | Cria ferramentas de **ciência / engenharia / matemática** | ❌ só a pasta dele |
| 🏠 Construtor — Lane C | **Grok** | Cria ferramentas de **dia a dia / nichos pessoais** (casa, beleza, pet, finanças, saúde, jogos) | ❌ só a pasta dele |
| 🧑‍🍳 Integrador / Expedidor | **Claude** | Registra na Caixa, roda selftest, builda o `.exe`, commita/pusha, mantém docs e prefixos | ✅ é o único |

*(Divisão sugerida pelo Claude; o Caio pode trocar quem faz o quê.)*

---

## 🥩 Estação Construtor (Cursor / Antigravity / Grok)

Você constrói **uma ferramenta por vez**, só dentro da **sua pasta nova** `C:\Users\caion\<pasta>`.

1. Escolha uma ideia da **sua lane** (tema) que ainda não existe (confira a lista em `BUILTIN` do
   `caixa.pyw` e nos `AGENTS*.md` — **leitura apenas, não edite**).
2. Escolha um **prefixo único** de 3–4 letras que não esteja na tabela de prefixos do
   `AGENTS_PROTOCOL.md` nem nos `ENTREGA.json` das pastas vizinhas.
3. Crie exatamente: `<px>_core.py` (lógica), `<px>_gui.pyw` (PyQt6, tema escuro padrão, com
   `def main()`), `test_<px>.py`. Siga o `AGENTS_PROTOCOL.md`.
4. Teste você mesmo: `py_compile` + teste de lógica + smoke GUI offscreen. Varra caracteres
   estranhos (0x0300–0x1CFF) nos seus arquivos.
5. **Quando terminar e passar nos testes, crie na pasta um arquivo `ENTREGA.json`** (modelo
   abaixo) com `status: "pronto"`. **PARE AQUI.** Não registre na Caixa, não builde, não edite os
   arquivos compartilhados — o Integrador faz isso.
6. Pegue a próxima ideia da sua lane.

### Modelo de `ENTREGA.json` (na raiz da sua pasta)
```json
{
  "pasta": "nome-da-pasta",
  "script": "px_gui.pyw",
  "prefixo": "px_",
  "emoji": "🧩",
  "nome": "Nome da Ferramenta",
  "descricao": "Descrição curta de uma frase.",
  "lane": "A|B|C",
  "status": "pronto"
}
```

**O que o construtor NUNCA faz:** editar `caixa.pyw`, `build_suite.py`, `AGENTS.md`,
`AGENTS_PROTOCOL.md`, `BACKLOG.md`, `CLAUDE.md`, nem rodar `build_suite.py` (build do exe).
Mexer em pasta que não é a sua. Dar push.

---

## 🧑‍🍳 Estação Integrador / Expedidor (Claude)

Roda em ciclos. A cada ciclo:

1. **Varre** as pastas irmãs procurando `ENTREGA.json` com `status: "pronto"` ainda não integrados.
2. Para cada um: confere os testes (`test_<px>.py`), `py_compile`, varredura de unicode, e se tem
   `def main()`.
3. **Registra** (único a fazer isso): tupla em `BUILTIN` (`caixa.pyw`) + entrada em `TOOLS`
   (`build_suite.py`) + prefixo na tabela do `AGENTS_PROTOCOL.md`/`AGENTS.md`.
4. Roda `build_suite.py --stage-only` + `staged\app.py --selftest` → tem que dar `OK: N`.
5. Marca o `ENTREGA.json` como `"status": "integrado"` e commita (pasta + integração).
6. Atualiza `AGENTS.md` (estado/log), `BACKLOG.md` e a memória.
7. **Build do `.exe`** e push: só quando o Caio pedir ("fecha versão") ou em marco grande.

---

## 🧭 Lanes (temas) pra não repetir ideia

- **Lane A (Cursor) — Sistema/Arquivos/Dev:** utilitários de Windows, arquivos, rede, automação,
  ferramentas de programação, formatos, linha de comando.
- **Lane B (Antigravity) — Ciência/Engenharia/Matemática:** física, química, elétrica, mecânica,
  estatística, geometria, algoritmos, simuladores.
- **Lane C (Grok) — Dia a dia/Pessoal:** casa e família, beleza, pet, plantas, cozinha, finanças
  pessoais, saúde, estudos, eventos, hobbies, jogos.

Se bater dúvida de a qual lane uma ideia pertence, o Integrador decide. Duas lanes nunca devem
produzir a mesma ferramenta — na dúvida, confira os `ENTREGA.json` das pastas vizinhas.

---

## ✅ Por que isso funciona (McDonald's)

- **Zero conflito nos arquivos compartilhados:** só o Integrador encosta neles.
- **Zero ideia repetida:** cada construtor tem uma lane de tema.
- **Zero build quebrado:** o Integrador valida tudo (`--selftest`) antes de commitar.
- **Entrega assíncrona:** construtor não espera ninguém — larga o `ENTREGA.json` e segue; o
  Integrador recolhe no ritmo dele. Igual cozinha: um frita, outro monta, outro entrega.

*Arquivo criado em 2026-11-08. Combinação dos 4 agentes da fábrica da Caixa de Ferramentas.*
