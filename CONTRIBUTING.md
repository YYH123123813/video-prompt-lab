# Contributing

Thanks for improving Video Prompt Lab.

Good contributions:

- model-specific style notes that improve prompt reliability
- ShotSpec examples for real production formats
- lint rules that prevent wasted video-generation credits
- evaluation rubrics for specific creator niches
- agent-skill improvements

Please avoid dumping random prompts. This project is about a reproducible workflow: structured brief, rendered prompt, lint report, generation, scorecard, iteration.

## Local verification

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
python3 -m compileall -q video_prompt_lab.py
python3 video_prompt_lab.py examples/product-ad.yaml --models veo,sora,kling,seedance --out /tmp/video-prompt-lab-sample
```
