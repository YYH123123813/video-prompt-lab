# Changelog

## v0.1.0 - 2026-05-12

First public release.

- Added ShotSpec YAML format for AI-video production briefs.
- Added Python CLI that renders model-specific prompts for Sora, Veo, Runway, Kling, Seedance/Jimeng, and generic models.
- Added prompt linting for common generation-credit-wasting failures.
- Added evaluation scorecard for comparing model outputs.
- Added examples for product ads, faceless shorts, mini-drama scenes, and China short-video workflows.
- Added an Agent Skill wrapper for agentic prompt-production workflows.

Verification:

- `python3 -m pytest -q` -> 4 passed
- `python3 -m compileall -q video_prompt_lab.py`
