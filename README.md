# Standing Wave Animation

A physics visualization built with **Manim Community 0.18.1**, exploring standing waves, energy density, energy flow, and phase on a fixed-end string.

The film uses staged equations and synchronized graphs, with Chinese captions. Final output is a silent 1080p video at 30 fps.

## Setup

Install [Conda](https://docs.conda.io/), a TeX distribution providing `latex` and `dvisvgm`, and a Chinese font. FFmpeg is included in the Conda environment.

```bash
conda env create -f environment.yml
conda activate wave-manim
```

The environment uses Python 3.11. Fonts default to Microsoft YaHei when available, with Droid Sans Fallback as a fallback; adjust `FONT` in `src/visuals.py` for other systems.

## Build

Run from the repository root:

```bash
# 720p preview
python scripts/render.py --quality preview

# 1080p final render
python scripts/render.py --quality final

# Validate the final export and generate a storyboard
python scripts/review.py
```

The render pipeline checks the physics and animation behavior, renders the scenes with Manim, and exports an MP4 with chapters and a separate SRT file to `output/`.

[Watch the film](output/standing_wave.mp4) · [View the storyboard](output/storyboard.jpg)

## Project Structure

```text
src/standing_wave.py     Scene choreography and equation transitions
src/visuals.py           Shared styles, plots, and timing helpers
narration/script.json    Caption text and timing
scripts/                Rendering and validation tools
manim.cfg               Manim renderer and video settings
environment.yml         Conda dependencies
docs/physics.md         Model assumptions and derivations
output/                 Exported video, captions, and review assets
```

Edit `narration/script.json` to change captions or cue durations, `src/standing_wave.py` to change the animation, and `manim.cfg` to adjust rendering settings. Intermediate files in `build/` and `media/` are excluded from Git.
