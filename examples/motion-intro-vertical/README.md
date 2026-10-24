# Exemplo: Apresentação Vertical em Português (cutroom-motion / HyperFrames 0.8.183 + Kokoro / Clone + earshot)

**Solicitação:** "Segunda versão do vídeo de apresentação na resolução pra celular (9:16 vertical, 1080×1920) em português brasileiro, com cards adaptados para mobile, narração em português e 19 efeitos sonoros procedurais via earshot."

<p align="center">
  <video src="out/intro-vertical-pt.mp4" controls preload="metadata" poster="out/sheet.png" width="450">
    <a href="out/intro-vertical-pt.mp4"><img src="out/preview.gif" width="450" alt="Assistir intro-vertical-pt.mp4 com narração e efeitos sonoros"></a>
  </video>
</p>
<p align="center">
  <a href="out/intro-vertical-pt.mp4"><strong>▶ Assistir &amp; ouvir com áudio (<code>out/intro-vertical-pt.mp4</code> · 27.30 s · 1080×1920 vertical)</strong></a>
</p>

[`out/intro-vertical-pt.mp4`](out/intro-vertical-pt.mp4) (27.30 s, 1080x1920 @ 30.0 fps, H.264 + AAC stereo, 2.21 MB) · [`out/sheet.png`](out/sheet.png) (contact sheet vertical) · [`out/sound-sheet.png`](out/sound-sheet.png) (folha de áudio earshot) · [`src/cues_pt.json`](src/cues_pt.json) (19 cues SFX procedurais) · fonte em [`src/intro/`](src/intro)

| Arquivo | Descrição |
|---|---|
| [`out/intro-vertical-pt.mp4`](out/intro-vertical-pt.mp4) | Entregável: vídeo vertical de 27.30 s com narração em português e 19 efeitos sonoros do `earshot` (2.21 MB) |
| [`out/preview.gif`](out/preview.gif) | GIF animado de demonstração para visualização rápida no GitHub (631 KB) |
| [`out/sheet.png`](out/sheet.png) | Folha de contato 4×3 com 12 keyframes verticais ao longo das 5 cenas |
| [`out/sound-sheet.png`](out/sound-sheet.png) | Espectrograma e curva de sincronia audiovisual gerados via `earshot sheet` |
| [`src/SCRIPT_PT.md`](src/SCRIPT_PT.md) | Roteiro oficial de produção em português brasileiro |
| [`src/speech_pt.txt`](src/speech_pt.txt) | Texto da fala extraído para síntese local |
| [`src/cues_pt.json`](src/cues_pt.json) | 19 marcações de efeitos sonoros calibrados |
| [`src/intro/index.html`](src/intro/index.html) | Composição HyperFrames 1080×1920 adaptada com stack vertical e animações GSAP |

## Estrutura Vertical (1080×1920) para Mobile

1. **Cena 1: Decks, Diagramas, 3D e Extração (0:00 - 6.00s)**
   - Stack vertical com 4 cards de capacidades em Night Plum (`#16072B`): barras crescendo (`cutroom-deck`), pulso de sinal de arquitetura (`cutroom-diagram`), gaveta 3D isométrica (`cutroom-iso3d`) e scanner laser de PDF (`cutroom-extract`).
2. **Cena 2: Vídeos, Marcas, Voz e Som (6.00 - 13.50s)**
   - Fundo Blush Paper (`#FFF7FA`): curva matemática com tangente e leitura viva $f'(x) = 1.25$, timeline multi-faixa GSAP, amostras de paleta de marca e espectrograma dinâmico de 24 barras com 252 sons do `earshot`.
3. **Cena 3: 6 Agentes Coding Suportados (13.50 - 20.50s)**
   - Grid 2×3 com os 6 agentes de coding (Claude Code, Cursor, Codex, Antigravity, Gemini, Kiro) e os 3 pilares de execução: 100% Local, Pinos Travados e Equipes em Paralelo.
4. **Cena 4: Instalação Descomplicada (20.50 - 26.50s)**
   - Terminal de chat mobile digitando `Configure https://github.com/galvaowesley/cutroom` com checagens automáticas de sucesso.
5. **Cena 5: Encerramento de Alto Contraste (26.50 - 28.00s)**
   - Tela cheia em Hot Signal (`#FF2D6F`) com wordmark oficial, slogan "Toda peça gerada na sua própria máquina" e URL do repositório.

## Como plugar a voz clonada (Wesley)

Assim que o arquivo `wesley.m4a` for colocado na pasta do repositório:

```bash
. ~/.local/share/cutroom/env.sh

# 1. Clonar a voz com o áudio gravado e consentimento
voice clone wesley --ref wesley.m4a --speaker "Wesley Galvão" \
  --consent "Autorização de Wesley Galvão para uso de voz no Cutroom, 2026-10-24" \
  --lang pt

# 2. Sintetizar a narração na voz clonada
tts -f src/speech_pt.txt -o src/intro/assets/narration-raw.m4a --voice clone:wesley --lang pt --pronounce src/pronounce_pt.json
cutroom edit loudnorm src/intro/assets/narration-raw.m4a -o src/intro/assets/narration.m4a --target -16

# 3. Renderizar com a sua voz
cd src/intro && hyperframes render --quality delivery --output ../../work/raw.mp4 && cd ../..
cutroom edit sfx work/raw.mp4 --cues src/cues_pt.json -o out/intro-vertical-pt.mp4
```
