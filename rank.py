#!/usr/bin/env python3
"""
Redrob Intelligent Candidate Ranking — Main Entry Point

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Produces a valid submission CSV (top 100 candidates ranked for the
Senior AI Engineer JD) in under 5 minutes on a 16GB CPU machine.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from honeypot_detector import is_honeypot
from scorer import score_candidate


def load_candidates(path: Path) -> List[Dict[str, Any]]:
    """Load candidates from a .jsonl file."""
    candidates = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                candidates.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  [WARN] Skipping malformed line {i+1}: {e}", file=sys.stderr)
    return candidates


def rank_candidates(
    candidates: List[Dict[str, Any]],
    verbose: bool = False,
) -> List[Tuple[str, int, float, str]]:
    """
    Score all candidates, detect honeypots, return top-100 ranked list.

    Returns list of (candidate_id, rank, score, reasoning).
    """
    t0 = time.time()
    scored: List[Tuple[float, str, str]] = []  # (score, cand_id, reasoning)
    honeypot_count = 0
    n = len(candidates)

    print(f"Scoring {n:,} candidates...", flush=True)

    for i, candidate in enumerate(candidates):
        if verbose and i % 10000 == 0:
            elapsed = time.time() - t0
            pct = i / n * 100
            eta = (elapsed / max(i, 1)) * (n - i)
            print(
                f"  [{pct:5.1f}%] {i:>6}/{n}  "
                f"elapsed={elapsed:.1f}s  eta={eta:.0f}s",
                flush=True,
            )

        cid = candidate.get("candidate_id", f"UNKNOWN_{i}")

        # ── Honeypot check ────────────────────────────────────────────────────
        flagged, hp_reason = is_honeypot(candidate)
        if flagged:
            honeypot_count += 1
            if verbose:
                print(f"  [HONEYPOT] {cid}: {hp_reason}", file=sys.stderr)
            # Assign a very low score so they never make top 100
            scored.append((-9.0, cid, f"EXCLUDED: {hp_reason[:80]}"))
            continue

        # ── Score ─────────────────────────────────────────────────────────────
        score, reasoning = score_candidate(candidate)
        scored.append((score, cid, reasoning))

    elapsed = time.time() - t0
    print(f"Scoring complete in {elapsed:.1f}s  |  honeypots detected: {honeypot_count}", flush=True)

    # ── Sort descending by score, then ascending by candidate_id for ties ─────
    scored.sort(key=lambda x: (-x[0], x[1]))

    # ── Take top 100 ──────────────────────────────────────────────────────────
    top100 = scored[:100]

    # ── Assign ranks & normalise scores to [0, 1] non-increasing ─────────────
    max_score = top100[0][0] if top100 else 1.0
    min_score_100 = top100[-1][0] if top100 else 0.0
    score_range = max_score - min_score_100 if max_score > min_score_100 else 1.0

    # Build (norm_score, raw_score, cid, reasoning) list
    norm_rows: List[Tuple[float, float, str, str]] = []
    for raw_score, cid, reasoning in top100:
        norm_score = 0.20 + 0.79 * (raw_score - min_score_100) / score_range
        norm_score = round(max(0.0, min(1.0, norm_score)), 4)
        norm_rows.append((norm_score, raw_score, cid, reasoning))

    # Within each group of equal norm_score, sort by candidate_id ascending
    # (spec tie-break rule). Groups are already score-descending from the
    # earlier sort, so we just need to stable-sort tied blocks by cid.
    norm_rows.sort(key=lambda x: (-x[0], x[2]))  # desc score, asc cid

    # Final monotone fix: ensure non-increasing (rounding can cause tiny upward steps)
    for i in range(1, len(norm_rows)):
        if norm_rows[i][0] > norm_rows[i - 1][0]:
            ns, rs, cid, rsn = norm_rows[i]
            norm_rows[i] = (norm_rows[i - 1][0], rs, cid, rsn)

    result: List[Tuple[str, int, float, str]] = [
        (cid, rank_idx + 1, ns, reasoning)
        for rank_idx, (ns, _, cid, reasoning) in enumerate(norm_rows)
    ]

    return result


def write_submission(
    rows: List[Tuple[str, int, float, str]],
    out_path: Path,
) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for cid, rank, score, reasoning in rows:
            # Ensure reasoning doesn't contain newlines (would break CSV)
            safe_reasoning = reasoning.replace("\n", " ").replace("\r", " ")
            writer.writerow([cid, rank, score, safe_reasoning])
    print(f"Submission written to: {out_path}  ({len(rows)} rows)", flush=True)


def print_preview(rows: List[Tuple[str, int, float, str]], n: int = 15) -> None:
    print(f"\n{'-'*90}")
    print(f"{'#':>3}  {'Candidate ID':<14}  {'Score':>6}  Reasoning")
    print(f"{'-'*90}")
    for cid, rank, score, reasoning in rows[:n]:
        print(f"{rank:>3}  {cid:<14}  {score:>6.4f}  {reasoning[:60]}")
    print(f"{'-'*90}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Rank top-100 candidates for the Redrob Senior AI Engineer JD."
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        required=True,
        help="Path to candidates.jsonl",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("submission.csv"),
        help="Output CSV path (default: submission.csv)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress every 10K candidates",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print top-15 preview after ranking",
    )
    args = parser.parse_args()

    if not args.candidates.exists():
        print(f"ERROR: candidates file not found: {args.candidates}", file=sys.stderr)
        sys.exit(1)

    t_start = time.time()

    print(f"\nRedrob Candidate Ranker - Senior AI Engineer JD")
    print(f"{'-'*50}")
    print(f"Input : {args.candidates}")
    print(f"Output: {args.out}\n")

    candidates = load_candidates(args.candidates)
    print(f"Loaded {len(candidates):,} candidates\n")

    rows = rank_candidates(candidates, verbose=args.verbose)

    if args.preview:
        print_preview(rows)

    write_submission(rows, args.out)

    total_time = time.time() - t_start
    print(f"Total time: {total_time:.1f}s")
    print(f"\nRun validator:  python validate_submission.py {args.out}")


if __name__ == "__main__":
    main()
