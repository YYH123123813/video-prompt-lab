import subprocess
import sys
from pathlib import Path

import pytest


def sample_spec_text():
    return """
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
""".strip()


def test_load_lint_and_render_model_prompt(tmp_path):
    from video_prompt_lab import lint_spec, load_spec_text, render_model_prompt

    spec = load_spec_text(sample_spec_text())
    issues = lint_spec(spec)
    assert issues == []

    veo_prompt = render_model_prompt(spec, "veo")
    assert "Neon Tea Launch" in veo_prompt
    assert "9:16" in veo_prompt
    assert "slow push-in" in veo_prompt
    assert "no distorted label text" in veo_prompt
    assert "Veo" in veo_prompt

    sora_prompt = render_model_prompt(spec, "sora")
    assert "Sora" in sora_prompt
    assert "first frame" in sora_prompt.lower()


def test_lint_flags_missing_operational_fields():
    from video_prompt_lab import lint_spec

    issues = lint_spec({"title": "Loose idea", "duration": "10s", "subject": {"product": "shoe"}})
    codes = {issue["code"] for issue in issues}
    assert "missing_aspect_ratio" in codes
    assert "missing_camera_movement" in codes
    assert "missing_first_frame" in codes
    assert "missing_negative_constraints" in codes


def test_yaml_aspect_ratio_is_not_coerced_to_sexagesimal_number():
    from video_prompt_lab import load_spec_text

    spec = load_spec_text("""
title: Ratio Test
aspect_ratio: 9:16
""")

    assert spec["aspect_ratio"] == "9:16"


def test_cli_writes_outputs(tmp_path):
    spec_path = tmp_path / "shot.yaml"
    out_dir = tmp_path / "out"
    spec_path.write_text(sample_spec_text(), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "video_prompt_lab.py", str(spec_path), "--models", "veo,sora", "--out", str(out_dir)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    veo_file = out_dir / "veo.md"
    sora_file = out_dir / "sora.md"
    scorecard = out_dir / "scorecard.md"
    assert veo_file.exists()
    assert sora_file.exists()
    assert scorecard.exists()
    assert "Neon Tea Launch" in veo_file.read_text(encoding="utf-8")
    assert "AI Video Eval Scorecard" in scorecard.read_text(encoding="utf-8")
