# Redrob — Intelligent Candidate Discovery & Ranking

**Team:** Kittu  
**Challenge:** India Runs Data & AI Challenge — Senior AI Engineer JD

## Overview

A fast, deterministic multi-signal ranker that scores 100,000 candidates against a Senior AI Engineer job description in under 5 minutes on CPU. No external APIs, no ML training, no GPU required.

## Approach

Six scoring components:

| Component | Weight | Description |
|-----------|--------|-------------|
| Skill Match | 35% | Tier-based AI/ML keyword matching (Tier A/B/C) with proficiency, endorsement, and duration weighting |
| Title/Headline | 20% | Title keyword matching + summary semantic keyword scoring |
| Career Depth | 15% | YoE fit (5–9y optimal), industry relevance, startup experience, production ML signals in descriptions |
| Education | 5% | Institution tier (1–4) + field relevance |
| Location | 5% | India Tier-1 cities preferred; relocation willingness factored |
| Behavioral Multiplier | ×0.1–1.15 | Recency, open-to-work, recruiter response rate, GitHub activity, notice period, salary fit |

Plus honeypot detection: 10 checks for impossible profiles (overlapping tenures, impossible YoE, expert skills with 0 months, etc.)

## Reproduce

```bash
pip install -r requirements.txt
python rank.py --candidates ./candidates.jsonl --out ./submission.csv --verbose --preview
```

## Validate

```bash
python validate_submission.py ./submission.csv
```

## Files

```
rank.py              — CLI entry point
scorer.py            — All scoring components
skills_config.py     — AI skill keywords & weights
honeypot_detector.py — Impossible profile detection
requirements.txt     — Dependencies (python-dateutil only)
submission_metadata.yaml
```

## Compute Environment

- Python 3.11 on Windows 11 Home
- CPU only, no GPU
- Runtime: ~60–90 seconds for 100K candidates
- RAM: < 4 GB
