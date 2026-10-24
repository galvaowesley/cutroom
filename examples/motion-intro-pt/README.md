# Exemplo: Apresentação Vertical em Português do Brasil (cutroom-motion / HyperFrames + Kokoro + earshot)

**Solicitação:** "deixar a fala do vídeo de apresentação na vertical com uma fala mais natural, sem pausas na animação, transições interessantes e modernas, zooms e outros recursos, com cadência; o último frame no ar por mais um tempinho", e depois: "é um português com sotaque americano, eu preciso do português brasileiro".

<p align="center">
  <a href="out/intro-vertical-pt.mp4"><img src="out/preview.gif" width="300" alt="Assistir intro-vertical-pt.mp4 com narração e efeitos sonoros"></a>
</p>
<p align="center">
  <a href="out/intro-vertical-pt.mp4"><strong>▶ Assistir &amp; ouvir com áudio (<code>out/intro-vertical-pt.mp4</code> · 34,4 s · 1080×1920 vertical · pf_dora)</strong></a> ·
  <a href="../motion-intro/"><strong>English version</strong></a>
</p>

[`out/intro-vertical-pt.mp4`](out/intro-vertical-pt.mp4) (34.4 s, 1080x1920 @ 30 fps, H.264 + AAC, 4.7 MB, -15 LUFS) · [`out/sheet.png`](out/sheet.png) (folha de contato) · [`out/sound-sheet.png`](out/sound-sheet.png) (folha de áudio do earshot) · [`out/last-frame.png`](out/last-frame.png) · [`out/intro-vertical-pt.srt`](out/intro-vertical-pt.srt) · [`src/cues_pt.json`](src/cues_pt.json) (96 cues, gerados por [`src/make_cues_pt.py`](src/make_cues_pt.py)) · [`src/SCRIPT_PT.md`](src/SCRIPT_PT.md) · composição em [`src/intro/`](src/intro)

## O que mudou nesta versão

- **Português do Brasil de verdade.** O sotaque americano vinha de um erro do harness: um preset como `pf_dora` herdava o idioma da configuração (`en`) e o texto em português passava pelo fonetizador do inglês. Agora o preset fala o idioma da própria voz (`pt-br`), e o dicionário de pronúncia foi reescrito para esse fonetizador (`skills` → "iskíus", `slides` → "eslaides", `motion` → "môuchon", `Cursor` → "Quérsor"). As grafias antigas ("esquíls", "Câtrum") só faziam sentido para o fonetizador do inglês.
- **Cadência natural.** Sete frases curtas na velocidade nativa (1.0), cada uma sintetizada de uma vez, com os respiros da pontuação dentro da frase e pausas de 0,45 a 0,85 s entre elas (0,75 s depois de "cutroom"). Nada passa por *time-stretch*. Falado como se diz: "pra", "pro", "três dê".
- **A imagem segue a voz.** Os tempos de cada palavra saem do áudio (`src/timing.py`: silêncios medidos e palavras distribuídas pelo número de fonemas) e a composição é gerada a partir deles (`src/build.py` + `src/intro.template.html`). Se a fala mudar, `timing.py`, `build.py` e `make_cues_pt.py` refazem tempos, animação e sons juntos.
- **A animação não para.** Cenas sobrepostas, grade deslizando, feed de cartões que sobe sem parar, câmera que aproxima de cada agente, empurrão lento no chat e na tela final. As pausas da voz são cobertas pela imagem.
- **Transições**: zoom através do anel de ícones e máscara circular (1→2), whip-pan com desfoque (2→3), push vertical com desfoque (3→4), máscara circular rosa (4→5).
- **Último quadro no ar**: a fala termina em 30,9 s e o vídeo segue até 34,4 s (3,5 s) com aproximação lenta, brilho na URL e o logo em tela.
- **Mote**: "Toda peça gerada na sua máquina." (sem vírgula, na fala e na tela).

## Padrão de animação no harness

As peças do estilo (anel de ícones com zoom-through, feed de foco, câmera sobre uma grade, digitação, contador, máscara circular, whip-pan, push vertical) estão em [`harness/cutroom_motionkit.js`](../../harness/cutroom_motionkit.js) (cópia em `src/intro/assets/`), e a narração com pausas naturais e tempos por palavra em [`harness/cutroom_timing.py`](../../harness/cutroom_timing.py), para qualquer idioma. O catálogo de padrões, o fluxo e o checklist estão em [`skills/cutroom-motion/references/dynamic-style.md`](../../skills/cutroom-motion/references/dynamic-style.md). Esta composição usa o kit e o render é idêntico ao da versão anterior ao kit (PSNR infinito).

## Como refazer

```bash
cd examples/motion-intro-pt
# 1. uma frase por arquivo em work/v4/ (s1.txt ... s7.txt) a partir de src/speech_pt.txt, depois
tts -f work/v4/s2.txt -o work/v4/v2.wav --voice pf_dora@1.0 --pronounce src/pronounce_pt.json   # e as demais
python3 src/timing.py          # monta a narração com as pausas e mede os tempos das palavras
python3 src/build.py           # gera src/intro/index.html
python3 src/make_cues_pt.py    # cues de som nos mesmos tempos
cutroom edit loudnorm work/v4/narr_raw.wav -o src/intro/assets/narration.m4a --target -16
cutroom edit sfx work/v4/narr_raw.wav --cues src/cues_pt.json --stem src/intro/assets/sfx.wav --stem-only -o src/intro/assets/sfx.wav
cd src/intro && hyperframes render --quality delivery --output ../../out/intro-vertical-pt.mp4
```

Conferência: `hyperframes snapshot`, `cutroom edit sheet` e `earshot sheet --cues` (94% dos cues a menos de 100 ms do evento). A pronúncia dos nomes em inglês segue o dicionário de [`src/pronounce_pt.json`](src/pronounce_pt.json) e foi verificada pelos fonemas, não de ouvido.


## Uma peça por idioma

Cada idioma tem o seu roteiro, fala, dicionário de pronúncia e cues, feitos pelo mesmo código. A versão em inglês está em [`../motion-intro`](../motion-intro/) (`src/SCRIPT.md`, `speech.txt`, `pronounce.json`, `cues.json`). Para outro idioma, copie uma pasta, traduza as frases em `src/timing.py` e o texto de `src/intro.template.html`, ajuste os índices das palavras em `src/build.py` e reescreva os nomes com `voice phonemes <voz> "<palavra>"`.
