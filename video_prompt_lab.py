#!/usr/bin/env python3
"""Video Prompt Lab: render model-specific AI-video prompts from one ShotSpec."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SUPPORTED_MODELS = {
    "sora": {
        "label": "Sora",
        "focus": "physical scene continuity, first-frame clarity, temporal coherence, and natural motion",
        "note": "Use concise cinematic language and avoid stacking too many simultaneous actions.",
    },
    "veo": {
        "label": "Veo",
        "focus": "cinematic realism, camera intent, lighting, and synced audio or sound-design cues",
        "note": "State the camera move, subject continuity anchor, and audio expectations explicitly.",
    },
    "runway": {
        "label": "Runway",
        "focus": "shot direction, motion strength, composition, and edit-friendly visual beats",
        "note": "Keep the shot compact and prioritize a strong visual transformation.",
    },
    "kling": {
        "label": "Kling",
        "focus": "character/object consistency, readable action, and natural camera movement",
        "note": "Describe the subject anchor and movement path in plain concrete language.",
    },
    "seedance": {
        "label": "Seedance / Jimeng",
        "focus": "vertical short-video rhythm, strong hook framing, subject consistency, and overlay-safe space",
        "note": "For China-style short video, reserve space for captions and make the first second instantly legible.",
    },
    "generic": {
        "label": "Generic AI video model",
        "focus": "clear subject, first frame, camera, motion, lighting, duration, and constraints",
        "note": "Use this fallback when a model-specific prompt style is unknown.",
    },
}

REQUIRED_TOP_LEVEL = ["title", "goal", "duration", "aspect_ratio", "subject", "scene", "camera"]


def _load_yaml(text: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError("PyYAML is required for ShotSpec YAML. Install with: python3 -m pip install pyyaml") from exc

    # Use BaseLoader instead of safe_load so production fields such as
    # `aspect_ratio: 9:16` stay as strings. PyYAML's default YAML 1.1
    # resolver otherwise treats unquoted ratios as sexagesimal numbers.
    data = yaml.load(text, Loader=yaml.BaseLoader)
    if not isinstance(data, dict):
        raise ValueError("ShotSpec must parse to a YAML mapping/object.")
    return data


def load_spec_text(text: str) -> dict[str, Any]:
    """Load a ShotSpec from YAML or JSON text."""
    stripped = text.strip()
    if not stripped:
        raise ValueError("ShotSpec text is empty.")
    if stripped.startswith("{"):
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError("ShotSpec JSON must be an object.")
        return data
    return _load_yaml(stripped)


def load_spec_file(path: str | Path) -> dict[str, Any]:
    return load_spec_text(Path(path).read_text(encoding="utf-8"))


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, dict):
        return [f"{key}: {val}" for key, val in value.items() if str(val).strip()]
    text = str(value).strip()
    return [text] if text else []


def _get(spec: dict[str, Any], path: str, default: Any = "") -> Any:
    current: Any = spec
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def _flat(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return "; ".join(f"{key}: {_flat(val)}" for key, val in value.items() if _flat(val))
    if isinstance(value, list):
        return "; ".join(str(item) for item in value if str(item).strip())
    return str(value).strip()


def lint_spec(spec: dict[str, Any]) -> list[dict[str, str]]:
    """Return operational prompt issues as dictionaries with code/message/fix."""
    issues: list[dict[str, str]] = []

    for field in REQUIRED_TOP_LEVEL:
        if not spec.get(field):
            issues.append(
                {
                    "code": f"missing_{field}",
                    "message": f"ShotSpec is missing top-level field `{field}`.",
                    "fix": f"Add `{field}` so every model output has a stable production brief.",
                }
            )

    if not spec.get("aspect_ratio"):
        issues.append(
            {
                "code": "missing_aspect_ratio",
                "message": "No aspect ratio is specified.",
                "fix": "Add `aspect_ratio`, for example `9:16`, `16:9`, or `1:1`.",
            }
        )

    camera_movement = _get(spec, "camera.movement") or _get(spec, "camera.move")
    if not camera_movement:
        issues.append(
            {
                "code": "missing_camera_movement",
                "message": "Camera movement is not specified.",
                "fix": "Add `camera.movement`, such as `slow push-in`, `locked tripod`, or `handheld follow`.",
            }
        )

    if not _get(spec, "scene.first_frame"):
        issues.append(
            {
                "code": "missing_first_frame",
                "message": "The first frame is not described.",
                "fix": "Add `scene.first_frame` so generation starts with a concrete visual anchor.",
            }
        )

    if not spec.get("negative_constraints"):
        issues.append(
            {
                "code": "missing_negative_constraints",
                "message": "No negative constraints are provided.",
                "fix": "Add a short `negative_constraints` list for common failure modes.",
            }
        )

    duration_text = str(spec.get("duration", ""))
    actions = _as_list(_get(spec, "motion.actions"))
    seconds_match = re.search(r"(\d+)", duration_text)
    if seconds_match and actions:
        seconds = int(seconds_match.group(1))
        if seconds <= 8 and len(actions) > 4:
            issues.append(
                {
                    "code": "too_many_actions_for_duration",
                    "message": f"{len(actions)} actions may be too many for {duration_text}.",
                    "fix": "Reduce actions or increase duration so the model can render a readable shot.",
                }
            )

    return _dedupe_issues(issues)


def _dedupe_issues(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for issue in issues:
        if issue["code"] in seen:
            continue
        seen.add(issue["code"])
        result.append(issue)
    return result


def render_model_prompt(spec: dict[str, Any], model: str) -> str:
    key = model.lower().strip()
    if key not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model `{model}`. Choose one of: {', '.join(SUPPORTED_MODELS)}")

    model_info = SUPPORTED_MODELS[key]
    label = model_info["label"]
    title = spec.get("title", "Untitled shot")
    actions = _as_list(_get(spec, "motion.actions"))
    overlays = _as_list(spec.get("text_overlays"))
    negatives = _as_list(spec.get("negative_constraints"))
    lint_issues = lint_spec(spec)

    sections = [
        f"# {label} Prompt — {title}",
        "",
        "## Production brief",
        f"Goal: {_flat(spec.get('goal')) or 'Not specified'}",
        f"Platform: {_flat(spec.get('platform')) or 'Not specified'}",
        f"Duration: {_flat(spec.get('duration')) or 'Not specified'}",
        f"Aspect ratio: {_flat(spec.get('aspect_ratio')) or 'Not specified'}",
        "",
        "## Model-specific direction",
        f"Optimize for {model_info['focus']}.",
        model_info["note"],
        "",
        "## Prompt",
        (
            f"Create a {spec.get('duration', 'short')} AI video in {spec.get('aspect_ratio', 'the requested aspect ratio')} "
            f"for {label}. The shot is titled \"{title}\". "
            f"The core objective is: {_flat(spec.get('goal')) or 'make the visual idea clear and emotionally legible'}."
        ),
        "",
        f"Subject and continuity anchor: {_flat(spec.get('subject')) or 'Not specified'}. "
        f"Keep this anchor stable across the entire shot: {_flat(spec.get('character_consistency')) or 'Not specified'}.",
        "",
        f"First frame: {_flat(_get(spec, 'scene.first_frame')) or 'Not specified'}. "
        f"Final frame: {_flat(_get(spec, 'scene.final_frame')) or 'Not specified'}. "
        f"Scene details: {_flat(spec.get('scene')) or 'Not specified'}.",
        "",
        f"Camera: framing = {_flat(_get(spec, 'camera.framing')) or 'Not specified'}; "
        f"movement = {_flat(_get(spec, 'camera.movement')) or 'Not specified'}.",
        "",
        f"Motion beats: {'; '.join(actions) if actions else 'Not specified'}.",
        f"Lighting and color: {_flat(spec.get('lighting')) or 'Not specified'}.",
        f"Audio/dialogue: {_flat(spec.get('audio_dialogue')) or 'Not specified'}.",
        f"Text overlays: {'; '.join(overlays) if overlays else 'None'}.",
        "",
        "Negative constraints: " + ("; ".join(negatives) if negatives else "avoid distorted anatomy, unreadable text, flicker, extra objects, and jump cuts"),
        "",
        "## Operator notes",
    ]

    if lint_issues:
        sections.append("Resolve these lint warnings before generating final assets:")
        for issue in lint_issues:
            sections.append(f"- {issue['code']}: {issue['message']} Fix: {issue['fix']}")
    else:
        sections.append("No lint warnings. This ShotSpec is ready for a first generation pass.")

    return "\n".join(sections).strip() + "\n"


def render_scorecard(spec: dict[str, Any], models: list[str]) -> str:
    title = spec.get("title", "Untitled shot")
    rows = [
        "# AI Video Eval Scorecard",
        "",
        f"ShotSpec: {title}",
        "",
        "Use this after generating videos from the prompts. Score each dimension from 1 to 5.",
        "",
        "| Model | Hook clarity | Subject consistency | Camera fidelity | Motion readability | Brand/story fit | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for model in models:
        label = SUPPORTED_MODELS.get(model, SUPPORTED_MODELS["generic"])["label"]
        rows.append(f"| {label} |  |  |  |  |  |  |")

    rows.extend(
        [
            "",
            "## Pass/fail checklist",
            "",
            "- [ ] First frame matches the ShotSpec.",
            "- [ ] The subject/character anchor stays consistent.",
            "- [ ] The camera movement is visible but not chaotic.",
            "- [ ] Motion beats fit the requested duration.",
            "- [ ] Text overlays are readable or intentionally absent.",
            "- [ ] Negative constraints were mostly respected.",
        ]
    )
    return "\n".join(rows).strip() + "\n"


def render_lint_report(spec: dict[str, Any]) -> str:
    issues = lint_spec(spec)
    if not issues:
        return "# Prompt Lint Report\n\nNo lint warnings.\n"
    lines = ["# Prompt Lint Report", ""]
    for issue in issues:
        lines.append(f"- **{issue['code']}**: {issue['message']} Fix: {issue['fix']}")
    return "\n".join(lines).strip() + "\n"


def write_outputs(spec: dict[str, Any], models: list[str], out_dir: str | Path) -> list[Path]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for model in models:
        key = model.lower().strip()
        path = output / f"{key}.md"
        path.write_text(render_model_prompt(spec, key), encoding="utf-8")
        written.append(path)
    scorecard = output / "scorecard.md"
    scorecard.write_text(render_scorecard(spec, models), encoding="utf-8")
    written.append(scorecard)
    lint_report = output / "lint-report.md"
    lint_report.write_text(render_lint_report(spec), encoding="utf-8")
    written.append(lint_report)
    return written


def parse_models(raw: str) -> list[str]:
    models = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not models:
        raise ValueError("At least one model is required.")
    unknown = [model for model in models if model not in SUPPORTED_MODELS]
    if unknown:
        raise ValueError(f"Unsupported model(s): {', '.join(unknown)}. Choose from: {', '.join(SUPPORTED_MODELS)}")
    return models


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate model-specific AI-video prompts from one ShotSpec YAML file.")
    parser.add_argument("spec", help="Path to a ShotSpec YAML or JSON file")
    parser.add_argument("--models", default="veo,sora,runway,kling,seedance", help="Comma-separated models to render")
    parser.add_argument("--out", default="outputs", help="Output directory")
    args = parser.parse_args(argv)

    try:
        spec = load_spec_file(args.spec)
        models = parse_models(args.models)
        written = write_outputs(spec, models, args.out)
    except Exception as exc:  # noqa: BLE001 - CLI should print friendly errors
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print("Video Prompt Lab wrote:")
    for path in written:
        print(f"- {path}")
    lint_count = len(lint_spec(spec))
    print(f"Lint warnings: {lint_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
