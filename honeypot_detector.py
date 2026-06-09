"""
Honeypot detection for impossible / fraudulent candidate profiles.
Honeypots in this dataset have subtly impossible profiles (per redrob_signals_doc).
Any candidate flagged here is forced to rank 101+ (excluded from top 100).
"""

from datetime import date, datetime
from typing import Dict, Any


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def is_honeypot(candidate: Dict[str, Any]) -> tuple[bool, str]:
    """
    Returns (is_honeypot: bool, reason: str).
    A candidate is a honeypot if ANY of these conditions are true.
    """
    today = date.today()
    cid = candidate.get("candidate_id", "?")
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})

    yoe = profile.get("years_of_experience", 0) or 0

    # ── 1. Experience exceeds career timeline ─────────────────────────────────
    # If total duration_months in career is wildly less than YoE * 12
    total_months = sum(r.get("duration_months", 0) or 0 for r in career)
    if yoe > 3 and total_months > 0:
        career_years = total_months / 12
        if yoe > career_years * 1.8 + 2:  # YoE inflated by >80%+2yrs
            return True, f"YoE ({yoe:.1f}y) grossly exceeds career timeline ({career_years:.1f}y)"

    # ── 2. Company existed shorter than stated tenure ─────────────────────────
    for role in career:
        start = parse_date(role.get("start_date"))
        end = parse_date(role.get("end_date")) or today
        duration_months = role.get("duration_months", 0) or 0
        if start and duration_months > 0:
            actual_months = (end.year - start.year) * 12 + (end.month - start.month)
            # Allow 2-month slack for rounding
            if duration_months > actual_months + 2 and duration_months > 12:
                return True, (
                    f"Role at {role.get('company', '?')} claims {duration_months}mo "
                    f"but dates only span {actual_months}mo"
                )

    # ── 3. Expert in skill with 0 months duration ─────────────────────────────
    expert_zero_duration = [
        s["name"] for s in skills
        if s.get("proficiency") == "expert" and s.get("duration_months", 1) == 0
    ]
    if len(expert_zero_duration) >= 2:
        return True, f"Expert in {len(expert_zero_duration)} skills with 0 months duration"

    # ── 4. Unrealistic number of expert skills ────────────────────────────────
    expert_skills = [s for s in skills if s.get("proficiency") == "expert"]
    if len(expert_skills) >= 9:
        return True, f"Claims expert in {len(expert_skills)} skills (unrealistic)"

    # ── 5. Perfect signal profile (too good to be true) ──────────────────────
    rr = signals.get("recruiter_response_rate", 0)
    icr = signals.get("interview_completion_rate", 0)
    oar = signals.get("offer_acceptance_rate", -1)
    completeness = signals.get("profile_completeness_score", 0)
    if rr == 1.0 and icr == 1.0 and oar == 1.0 and completeness == 100:
        return True, "Impossible perfect behavioral signals (response=1.0, interview=1.0, offers=1.0, completeness=100)"

    # ── 6. Future signup date ─────────────────────────────────────────────────
    signup = parse_date(signals.get("signup_date"))
    if signup and signup > today:
        return True, f"Signup date {signup} is in the future"

    # ── 7. Last active before signup ─────────────────────────────────────────
    last_active = parse_date(signals.get("last_active_date"))
    if signup and last_active and last_active < signup:
        return True, f"Last active ({last_active}) before signup ({signup})"

    # ── 8. Overlapping roles (two concurrent full-time positions at 100%) ─────
    # Find roles that substantially overlap
    if len(career) >= 2:
        overlaps = 0
        for i in range(len(career)):
            r1 = career[i]
            s1 = parse_date(r1.get("start_date"))
            e1 = parse_date(r1.get("end_date")) or today
            for j in range(i + 1, len(career)):
                r2 = career[j]
                s2 = parse_date(r2.get("start_date"))
                e2 = parse_date(r2.get("end_date")) or today
                if s1 and s2 and e1 and e2:
                    # Overlap in months
                    overlap_start = max(s1, s2)
                    overlap_end = min(e1, e2)
                    if overlap_start < overlap_end:
                        overlap_months = (
                            (overlap_end.year - overlap_start.year) * 12
                            + (overlap_end.month - overlap_start.month)
                        )
                        if overlap_months > 12:  # >1 year overlap = suspicious
                            overlaps += 1
        if overlaps >= 2:
            return True, f"Multiple severely overlapping full-time roles ({overlaps} pairs)"

    # ── 9. Experience starts before plausible work age ────────────────────────
    # Oldest role shouldn't start before ~age 18 = birth ~(today - YoE - 18) years
    if career:
        oldest_start = min(
            (parse_date(r.get("start_date")) for r in career if r.get("start_date")),
            default=None,
        )
        if oldest_start:
            implied_birth_year = oldest_start.year - 18
            if implied_birth_year < 1950 or implied_birth_year > 2005:
                return True, f"Career start implies implausible birth year {implied_birth_year}"

    # ── 10. YoE far exceeds what's possible given education end year ──────────
    education = candidate.get("education", [])
    if education and yoe > 2:
        latest_grad = max(
            (e.get("end_year", 0) for e in education if e.get("end_year")),
            default=None,
        )
        if latest_grad:
            max_possible_yoe = today.year - latest_grad + 1
            if yoe > max_possible_yoe + 3:  # 3-year slack for gaps
                return True, (
                    f"YoE ({yoe:.1f}y) exceeds max possible since graduation "
                    f"({latest_grad}, max ~{max_possible_yoe}y)"
                )

    return False, ""
