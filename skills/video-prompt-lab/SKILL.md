---
name: video-prompt-lab
description: Generate, lint, and evaluate model-specific AI-video prompts from a ShotSpec YAML brief.
---

# Video Prompt Lab Skill

Use when a user wants prompts for Sora, Veo, Runway, Kling, Seedance, Jimeng, or a generic AI-video model.

Workflow:

1. Convert the idea into a ShotSpec YAML with title, goal, duration, aspect ratio, subject, scene, camera, motion, lighting, audio/dialogue, overlays, and negative constraints.
2. Run `python3 video_prompt_lab.py <spec.yaml> --models veo,sora,kling,seedance --out outputs/<name>`.
3. Review `lint-report.md` before spending generation credits.
4. Give the user the model-specific prompt files.
5. After generation, fill `scorecard.md` and iterate based on the weakest dimension.

Do not treat prompt generation as final output. Treat it as a measurable production loop.
