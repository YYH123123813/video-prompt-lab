# Video Prompt Lab

Generate model-specific AI-video prompts from one structured ShotSpec.

`idea -> ShotSpec YAML -> Sora / Veo / Runway / Kling / Seedance prompts -> lint report -> eval scorecard`

This is a local-first prompt ops kit for AI-video creators, short-form content teams, and coding agents. It is not another static list of prompts. It gives you a repeatable workflow: describe the shot once, render model-specific prompts, check common failure modes, and compare outputs with a scorecard.

## Why this exists

AI-video prompts are becoming production assets. A good prompt needs more than a vibe:

- a concrete first frame
- duration and aspect ratio
- stable subject or character anchors
- camera framing and movement
- readable motion beats
- audio / dialogue expectations
- text overlay constraints
- negative constraints for common artifacts
- an evaluation loop after generation

Video Prompt Lab turns those requirements into a small, version-controlled workflow that works without API keys.

## Quick start

```bash
git clone https://github.com/YYH123123813/video-prompt-lab.git
cd video-prompt-lab
python3 -m pip install -r requirements.txt
python3 video_prompt_lab.py examples/product-ad.yaml --models veo,sora,kling,seedance --out outputs/product-ad
```

You will get:

```text
outputs/product-ad/veo.md
outputs/product-ad/sora.md
outputs/product-ad/kling.md
outputs/product-ad/seedance.md
outputs/product-ad/scorecard.md
outputs/product-ad/lint-report.md
```

## ShotSpec format

A ShotSpec is a compact YAML production brief:

```yaml
title: Neon Tea Launch
goal: Launch a premium bottled tea in a 9:16 short ad.
platform: TikTok / Reels
duration: 8s
aspect_ratio: 9:16
subject:
  product: Glass bottle of sparkling oolong tea
  setting: Rainy neon street market at night
character_consistency:
  anchor: Same transparent bottle, gold cap, green label in every shot
scene:
  first_frame: Bottle on wet black stone, neon signs reflected in puddles
  final_frame: Hand picks up the bottle; condensation catches light
camera:
  framing: macro close-up into medium product reveal
  movement: slow push-in, then slight handheld lift
motion:
  actions:
    - condensation runs down the bottle
    - neon reflections ripple in the puddle
lighting: teal and amber neon, glossy highlights
audio_dialogue:
  music: soft future-garage pulse
  sfx: rain, bottle cap click
text_overlays:
  - Cold oolong. City energy.
negative_constraints:
  - no distorted label text
  - no extra bottles
```

## Supported output styles

- `sora` — physical scene continuity, first-frame clarity, temporal coherence
- `veo` — cinematic realism, camera intent, lighting, synced audio cues
- `runway` — shot direction, motion strength, edit-friendly visual beats
- `kling` — subject consistency, readable actions, natural camera movement
- `seedance` — vertical short-video rhythm, overlay-safe composition, hook-first framing
- `generic` — fallback prompt for other video models

## Prompt lint rules

The built-in linter flags operational gaps before you spend credits:

- missing aspect ratio
- missing camera movement
- missing first-frame description
- missing negative constraints
- too many motion beats for a short duration
- missing required production fields

## Evaluation loop

After generation, fill the scorecard for each model:

| Dimension | What to check |
| --- | --- |
| Hook clarity | Is the first second instantly understandable? |
| Subject consistency | Did the character/product stay stable? |
| Camera fidelity | Did the model respect framing and movement? |
| Motion readability | Are the actions readable within the duration? |
| Brand/story fit | Does the output serve the goal? |

This makes prompt iteration measurable instead of purely subjective.

## Examples

- `examples/product-ad.yaml` — vertical product commercial
- `examples/faceless-youtube-short.yaml` — faceless explainer / YouTube Short
- `examples/mini-drama-scene.yaml` — character-consistent short drama beat
- `examples/china-short-video.yaml` — China short-video template with Chinese overlay fields

The repo is English-first, with one localized China short-video example for Douyin / Xiaohongshu / Jimeng-style workflows.

## Agent Skill usage

Agents can use `skills/video-prompt-lab/SKILL.md` as a procedural wrapper:

1. Ask for or draft a ShotSpec.
2. Run the linter.
3. Generate model-specific prompts.
4. Hand the user the prompt files and scorecard.
5. Iterate from scored outputs.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local verification and contribution guidelines.

Useful contributions:

- new model style notes
- more ShotSpec examples
- better lint rules
- evaluation rubrics for specific niches
- prompt templates for real production formats

Please avoid adding random prompt dumps. The goal is a reproducible workflow.

## License

MIT
