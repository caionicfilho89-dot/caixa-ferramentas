# 🧰 Caixa de Ferramentas

Um app só que reúne **16 ferramentas** num lugar. Clique num cartão e a ferramenta abre. Tudo offline, feito em Python + PyQt6.

![16 ferramentas](https://img.shields.io/badge/ferramentas-16-7c5cff)

## As ferramentas

| | | |
|---|---|---|
| 📄 Kit de PDF | 🧹 Faxina de Disco | ♻️ Recupera Arquivos |
| 🧽 Limpar Metadados | 🔳 QR Code | ✏️ Print Anotador |
| 🖼️ Conversor de Imagens | 🔐 Cofre de Senhas | 🎥 Gravador de Tela |
| 🎵 Conversor Áudio/Vídeo | 🎨 Capturador de Cores | 📝 Extrator de Texto (OCR) |
| 🔍 Busca de Arquivos | ✎ Renomeador em Lote | 📋 Área de Transferência |
| ⏱️ Rastreador de Tempo | | |

## Como usar

1. Tenha as ferramentas nas pastas ao lado desta (cada uma é um projeto próprio).
2. Instale o PyQt6:
   ```
   pip install -r requirements.txt
   ```
3. Rode:
   ```
   pythonw caixa.pyw
   ```
4. Clique no botão **📌 Atalho no Menu Iniciar** pra abrir a Caixa de qualquer lugar depois.

## Como funciona

Cada ferramenta roda no **seu próprio processo** (a Caixa só as abre), então uma não interfere na outra — é robusto e fácil de manter. Cada ferramenta tem seu próprio repositório e suas próprias dependências (veja o README de cada uma).

Pra adicionar uma ferramenta nova, basta uma linha na lista `TOOLS` dentro de `caixa.pyw`.

## Requisitos

- Windows 10/11
- Python 3.10+
- `PyQt6` (a Caixa em si). Cada ferramenta pode pedir libs extras no seu próprio `requirements.txt`.

## Licença

MIT — veja [LICENSE](LICENSE).
