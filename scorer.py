"""
Scoring engine for the Redrob Senior AI Engineer JD ranking challenge.

Components (all return 0.0 – 1.0 before weighting):
  1. skill_score        weight=0.35
  2. title_score        weight=0.20
  3. career_score       weight=0.15
  4. edu_score          weight=0.05
  5. location_score     weight=0.05
  6. engagement_mult    applied as multiplier (0.20 – 1.10) on above weighted sum

Final = (weighted_sum) × engagement_mult
"""

from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

from skills_config import (
    TIER_A_SKILLS,
    TIER_B_SKILLS,
    TIER_C_SKILLS,
    TIER_WEIGHTS,
    PROFICIENCY_MULT,
    TITLE_SCORES,
    SUMMARY_KEYWORDS,
    INDUSTRY_SCORES,
    INDIA_TIER1_CITIES,
    INDIA_TIER2_CITIES,
    SALARY_MIN_EXPECTED,
    SALARY_MAX_BUDGET,
    PRODUCTION_ML_SIGNALS,
    RESEARCH_ANTI_SIGNALS,
)

# ── Weights for final composite ───────────────────────────────────────────────
COMPONENT_WEIGHTS = {
    "skill":    0.35,
    "title":    0.20,
    "career":   0.15,
    "edu":      0.05,
    "location": 0.05,
    # The remaining 0.20 is implicitly the behavioral engagement multiplier's
    # headroom — it can push scores up or pull them down.
}

# Maximum raw skill score before normalisation (tuned empirically)
MAX_RAW_SKILL = 25.0

# ─────────────────────────────────────────────────────────────────────────────

def _lc(text: str) -> str:
    return text.lower()


def _today() -> date:
    return date.today()


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _clamp(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation: t=0 → a, t=1 → b."""
    t = _clamp(t)
    return a + (b - a) * t


# ─────────────────────────────────────────────────────────────────────────────
# 1. SKILL SCORE
# ─────────────────────────────────────────────────────────────────────────────

def _skill_tier(skill_name_lc: str) -> str | None:
    """Return 'A', 'B', 'C', or None."""
    for keyword in TIER_A_SKILLS:
        if keyword in skill_name_lc:
            return "A"
    for keyword in TIER_B_SKILLS:
        if keyword in skill_name_lc:
            return "B"
    for keyword in TIER_C_SKILLS:
        if keyword in skill_name_lc:
            return "C"
    return None


def score_skills(candidate: Dict[str, Any]) -> Tuple[float, Dict]:
    """
    Returns (normalised_score 0-1, breakdown dict).
    """
    skills: List[Dict] = candidate.get("skills", [])
    signals: Dict = candidate.get("redrob_signals", {})
    assessment_scores: Dict = signals.get("skill_assessment_scores", {})

    raw = 0.0
    tier_counts = {"A": 0, "B": 0, "C": 0}
    matched_skills = []

    for skill in skills:
        name_lc = _lc(skill.get("name", ""))
        tier = _skill_tier(name_lc)
        if tier is None:
            continue

        proficiency = skill.get("proficiency", "intermediate")
        prof_mult = PROFICIENCY_MULT.get(proficiency, 1.0)

        endorsements = skill.get("endorsements", 0) or 0
        endorse_mult = 1.0 + min(endorsements / 100, 0.3)  # up to +30%

        duration_months = skill.get("duration_months", 0) or 0
        dur_mult = 1.0
        if duration_months >= 36:
            dur_mult = 1.25
        elif duration_months >= 24:
            dur_mult = 1.15
        elif duration_months >= 12:
            dur_mult = 1.05
        elif duration_months == 0 and proficiency in ("advanced", "expert"):
            dur_mult = 0.7  # claimed proficiency with no duration is suspect

        # Platform assessment bonus
        assess_bonus = 0.0
        for assess_name, assess_score in assessment_scores.items():
            if _lc(assess_name) in name_lc or name_lc in _lc(assess_name):
                assess_bonus = (assess_score / 100) * 0.5
                break

        tier_weight = TIER_WEIGHTS[tier]
        contribution = tier_weight * prof_mult * endorse_mult * dur_mult + assess_bonus

        raw += contribution
        tier_counts[tier] += 1
        matched_skills.append(name_lc)

    # Bonus: having at least N Tier-A skills
    if tier_counts["A"] >= 5:
        raw *= 1.15
    elif tier_counts["A"] >= 3:
        raw *= 1.08

    # Penalty: very few AI skills but lots of unrelated ones
    total_ai = tier_counts["A"] + tier_counts["B"]
    if total_ai == 0:
        raw *= 0.3

    normalised = _clamp(raw / MAX_RAW_SKILL)
    return normalised, {
        "tier_A": tier_counts["A"],
        "tier_B": tier_counts["B"],
        "tier_C": tier_counts["C"],
        "matched": matched_skills[:8],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. TITLE / HEADLINE SCORE
# ─────────────────────────────────────────────────────────────────────────────

def score_title(candidate: Dict[str, Any]) -> Tuple[float, str]:
    profile = candidate.get("profile", {})
    title = _lc(profile.get("current_title", ""))
    headline = _lc(profile.get("headline", ""))
    summary = _lc(profile.get("summary", ""))

    # Direct title match
    title_score = 0.0
    for kw, sc in TITLE_SCORES.items():
        if kw in title:
            title_score = max(title_score, sc)

    # Headline scan
    headline_score = 0.0
    for kw, sc in TITLE_SCORES.items():
        if kw in headline:
            headline_score = max(headline_score, sc * 0.9)

    # Summary keyword scoring
    summary_raw = 0.0
    for kw, weight in SUMMARY_KEYWORDS.items():
        count = summary.count(kw) + headline.count(kw)
        if count > 0:
            summary_raw += weight * min(count, 3)  # cap at 3 mentions

    # Normalise summary contribution (typical range 0-20)
    summary_score = _clamp(summary_raw / 20.0) * 0.4

    # Production signal scan
    prod_hits = sum(1 for sig in PRODUCTION_ML_SIGNALS if sig in summary)
    prod_bonus = _clamp(prod_hits / 8.0) * 0.1

    # Research anti-signal
    research_penalty = sum(1 for sig in RESEARCH_ANTI_SIGNALS if sig in summary) * 0.05

    combined = (
        max(title_score, headline_score) * 0.5
        + summary_score
        + prod_bonus
        - research_penalty
    )

    return _clamp(combined), title


# ─────────────────────────────────────────────────────────────────────────────
# 3. CAREER SCORE
# ─────────────────────────────────────────────────────────────────────────────

def score_career(candidate: Dict[str, Any]) -> Tuple[float, str]:
    profile = candidate.get("profile", {})
    career: List[Dict] = candidate.get("career_history", [])
    yoe = profile.get("years_of_experience", 0) or 0

    # ── YoE fit ──────────────────────────────────────────────────────────────
    # Optimal range per JD: 5-9 years
    if yoe < 2:
        yoe_score = 0.1
    elif yoe < 4:
        yoe_score = _lerp(0.25, 0.65, (yoe - 2) / 2)
    elif yoe < 5:
        yoe_score = _lerp(0.65, 0.85, (yoe - 4))
    elif yoe <= 9:
        yoe_score = _lerp(0.85, 1.0, (yoe - 5) / 4)
    elif yoe <= 13:
        yoe_score = _lerp(1.0, 0.80, (yoe - 9) / 4)
    else:
        yoe_score = _lerp(0.80, 0.60, min((yoe - 13) / 7, 1))

    # ── Company / industry relevance ─────────────────────────────────────────
    industry_scores = []
    startup_bonus = 0.0
    prod_ml_score = 0.0

    for role in career:
        industry_lc = _lc(role.get("industry", ""))
        role_score = 0.0
        for ind, sc in INDUSTRY_SCORES.items():
            if ind in industry_lc:
                role_score = max(role_score, sc)
        if role_score == 0.0:
            role_score = 0.35  # unknown industry: neutral-low
        industry_scores.append(role_score)

        # Startup bonus (small company = more likely hands-on ML)
        company_size = role.get("company_size", "")
        if company_size in ("1-10", "11-50", "51-200"):
            startup_bonus = max(startup_bonus, 0.15)
        elif company_size in ("201-500",):
            startup_bonus = max(startup_bonus, 0.08)

        # Production ML signals in job description text
        desc_lc = _lc(role.get("description", ""))
        prod_hits = sum(1 for sig in PRODUCTION_ML_SIGNALS if sig in desc_lc)
        role_prod = _clamp(prod_hits / 6.0)
        prod_ml_score = max(prod_ml_score, role_prod)

    avg_industry = sum(industry_scores) / len(industry_scores) if industry_scores else 0.35

    # ── Title progression (seniority) ────────────────────────────────────────
    senior_count = sum(
        1 for r in career
        if any(t in _lc(r.get("title", "")) for t in ["senior", "lead", "staff", "principal", "head", "founding"])
    )
    senior_bonus = min(senior_count * 0.08, 0.20)

    career_raw = (
        yoe_score * 0.4
        + avg_industry * 0.25
        + prod_ml_score * 0.25
        + startup_bonus
        + senior_bonus
    )

    career_note = f"{yoe:.1f}y exp; {len(career)} roles"
    return _clamp(career_raw), career_note


# ─────────────────────────────────────────────────────────────────────────────
# 4. EDUCATION SCORE
# ─────────────────────────────────────────────────────────────────────────────

def score_education(candidate: Dict[str, Any]) -> float:
    education = candidate.get("education", [])
    if not education:
        return 0.30  # no education data — don't penalize too hard

    TIER_SCORE = {"tier_1": 1.0, "tier_2": 0.75, "tier_3": 0.45, "tier_4": 0.25, "unknown": 0.35}
    RELEVANT_FIELDS = {
        "computer science", "cs", "software", "artificial intelligence", "machine learning",
        "data science", "statistics", "mathematics", "electrical engineering",
        "electronics", "information technology", "it",
    }
    ADVANCED_DEGREES = {"m.tech", "mtech", "m.s.", "ms", "m.e.", "me", "m.sc", "msc", "phd", "ph.d"}

    best_tier_score = 0.0
    field_bonus = 0.0
    degree_bonus = 0.0

    for edu in education:
        tier = edu.get("tier", "unknown")
        tier_sc = TIER_SCORE.get(tier, 0.35)
        best_tier_score = max(best_tier_score, tier_sc)

        field_lc = _lc(edu.get("field_of_study", ""))
        if any(f in field_lc for f in RELEVANT_FIELDS):
            field_bonus = max(field_bonus, 0.15)

        degree_lc = _lc(edu.get("degree", ""))
        if any(d in degree_lc for d in ADVANCED_DEGREES):
            degree_bonus = max(degree_bonus, 0.10)

    return _clamp(best_tier_score * 0.75 + field_bonus + degree_bonus)


# ─────────────────────────────────────────────────────────────────────────────
# 5. LOCATION SCORE
# ─────────────────────────────────────────────────────────────────────────────

def score_location(candidate: Dict[str, Any]) -> float:
    profile = candidate.get("profile", {})
    country = _lc(profile.get("country", ""))
    location = _lc(profile.get("location", ""))
    signals = candidate.get("redrob_signals", {})
    relocate = signals.get("willing_to_relocate", False)

    in_india = "india" in country
    in_tier1 = any(city in location for city in INDIA_TIER1_CITIES)
    in_tier2 = any(city in location for city in INDIA_TIER2_CITIES)

    if in_india and in_tier1:
        return 1.0
    elif in_india and in_tier2:
        return 0.80
    elif in_india:
        return 0.70
    elif relocate:
        return 0.45  # willing to relocate from abroad
    else:
        return 0.10  # not in India, not willing to relocate


# ─────────────────────────────────────────────────────────────────────────────
# 6. BEHAVIORAL ENGAGEMENT MULTIPLIER
# ─────────────────────────────────────────────────────────────────────────────

def engagement_multiplier(candidate: Dict[str, Any]) -> Tuple[float, str]:
    signals = candidate.get("redrob_signals", {})
    today = _today()

    mult = 1.0
    notes = []

    # ── Recency of activity ───────────────────────────────────────────────────
    last_active = _parse_date(signals.get("last_active_date"))
    if last_active:
        days_inactive = (today - last_active).days
        if days_inactive > 365:
            mult *= 0.25
            notes.append("inactive >1yr")
        elif days_inactive > 180:
            mult *= 0.45
            notes.append("inactive >6mo")
        elif days_inactive > 90:
            mult *= 0.65
            notes.append("inactive >3mo")
        elif days_inactive > 30:
            mult *= 0.85
        # else: active within 30d — no penalty

    # ── Open to work ──────────────────────────────────────────────────────────
    open_to_work = signals.get("open_to_work_flag", False)
    if not open_to_work:
        mult *= 0.55
        notes.append("not open to work")

    # ── Recruiter response rate ───────────────────────────────────────────────
    rr = signals.get("recruiter_response_rate", 0.5)
    if rr < 0.05:
        mult *= 0.50
        notes.append(f"response_rate={rr:.2f}")
    elif rr < 0.15:
        mult *= 0.70
    elif rr < 0.30:
        mult *= 0.85
    else:
        mult *= _lerp(0.90, 1.05, (rr - 0.30) / 0.70)

    # ── Interview completion rate ─────────────────────────────────────────────
    icr = signals.get("interview_completion_rate", 0.5)
    if icr < 0.3:
        mult *= 0.70
        notes.append(f"interview_rate={icr:.2f}")
    elif icr < 0.6:
        mult *= 0.88
    else:
        mult *= _lerp(0.95, 1.02, (icr - 0.6) / 0.4)

    # ── Offer acceptance rate ─────────────────────────────────────────────────
    oar = signals.get("offer_acceptance_rate", -1)
    if oar != -1:
        if oar < 0.2:
            mult *= 0.80
        elif oar > 0.8:
            mult *= 1.02

    # ── Notice period ─────────────────────────────────────────────────────────
    notice = signals.get("notice_period_days", 60)
    if notice > 120:
        mult *= 0.82
        notes.append(f"notice={notice}d")
    elif notice <= 15:
        mult *= 1.03  # immediately available = bonus
    elif notice <= 30:
        mult *= 1.01

    # ── Work mode preference ──────────────────────────────────────────────────
    # Role is Hybrid in India
    work_mode = signals.get("preferred_work_mode", "flexible")
    if work_mode == "flexible" or work_mode == "hybrid":
        pass  # perfect match
    elif work_mode == "onsite":
        mult *= 0.97
    elif work_mode == "remote":
        mult *= 0.88

    # ── GitHub activity ───────────────────────────────────────────────────────
    github = signals.get("github_activity_score", -1)
    if github == -1:
        mult *= 0.92  # no GitHub — slight concern for AI engineer
    elif github > 75:
        mult *= 1.08
    elif github > 50:
        mult *= 1.04
    elif github < 10:
        mult *= 0.95

    # ── Profile completeness ──────────────────────────────────────────────────
    completeness = signals.get("profile_completeness_score", 70)
    if completeness < 40:
        mult *= 0.85
    elif completeness > 85:
        mult *= 1.02

    # ── Salary alignment ──────────────────────────────────────────────────────
    salary = signals.get("expected_salary_range_inr_lpa", {})
    sal_min = salary.get("min", 0) or 0
    sal_max = salary.get("max", 0) or 0
    if sal_min > SALARY_MAX_BUDGET:
        mult *= 0.70  # too expensive for Series A
        notes.append(f"salary_min={sal_min}L (over budget)")
    elif sal_max < SALARY_MIN_EXPECTED and sal_max > 0:
        mult *= 0.85  # very low expectations (may not be senior-level)

    # ── Verified identity signals ─────────────────────────────────────────────
    verified_bonus = 0.0
    if signals.get("verified_email"):
        verified_bonus += 0.01
    if signals.get("verified_phone"):
        verified_bonus += 0.01
    if signals.get("linkedin_connected"):
        verified_bonus += 0.01
    mult = min(mult + verified_bonus, 1.15)

    # ── Platform engagement ───────────────────────────────────────────────────
    search_30d = signals.get("search_appearance_30d", 0) or 0
    saved_30d = signals.get("saved_by_recruiters_30d", 0) or 0
    if saved_30d >= 3:
        mult = min(mult * 1.04, 1.15)
    if search_30d >= 20:
        mult = min(mult * 1.02, 1.15)

    note_str = "; ".join(notes) if notes else "good engagement"
    return _clamp(mult, 0.10, 1.15), note_str


# ─────────────────────────────────────────────────────────────────────────────
# MASTER SCORE FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def score_candidate(candidate: Dict[str, Any]) -> Tuple[float, str]:
    """
    Returns (final_score 0-1, reasoning string).
    """
    skill_sc, skill_detail = score_skills(candidate)
    title_sc, title_note = score_title(candidate)
    career_sc, career_note = score_career(candidate)
    edu_sc = score_education(candidate)
    loc_sc = score_location(candidate)
    eng_mult, eng_note = engagement_multiplier(candidate)

    base = (
        skill_sc    * COMPONENT_WEIGHTS["skill"]
        + title_sc  * COMPONENT_WEIGHTS["title"]
        + career_sc * COMPONENT_WEIGHTS["career"]
        + edu_sc    * COMPONENT_WEIGHTS["edu"]
        + loc_sc    * COMPONENT_WEIGHTS["location"]
    )

    final = _clamp(base * eng_mult)

    # ── Build reasoning ───────────────────────────────────────────────────────
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience", 0) or 0
    current_title = profile.get("current_title", "")
    location = profile.get("location", "")
    country = profile.get("country", "")
    loc_display = f"{location}, {country}" if location and country else location or country

    tier_a = skill_detail["tier_A"]
    tier_b = skill_detail["tier_B"]
    top_skills = ", ".join(skill_detail["matched"][:4]) if skill_detail["matched"] else "—"

    signals = candidate.get("redrob_signals", {})
    rr = signals.get("recruiter_response_rate", 0)
    notice = signals.get("notice_period_days", 60)
    github = signals.get("github_activity_score", -1)
    github_str = f"GitHub {github:.0f}/100" if github >= 0 else "no GitHub"

    reasoning_parts = [
        f"{current_title} with {yoe:.1f}y exp",
        f"{tier_a} core AI skills ({top_skills})",
        f"loc: {loc_display}",
        f"response rate {rr:.0%}",
        f"notice {notice}d",
        github_str,
    ]
    if eng_note and eng_note != "good engagement":
        reasoning_parts.append(eng_note)

    reasoning = "; ".join(p for p in reasoning_parts if p)

    return round(final, 6), reasoning
