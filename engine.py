"""Clearance's analysis engine.

Two layers, deliberately separated:

  * The *checks* (readability, accessibility, label hygiene) are real
    computation. They parse the drafted artifact and score the actual
    user-facing strings. Nothing here is pre-baked, and they will happily
    fail a message this repo wrote itself.

  * The *drafting* is deterministic by default so the demo runs anywhere
    with no key, no network and no cost. Set ANTHROPIC_API_KEY to have a
    real model draft instead; the same checks then run over its output,
    which is the point — the governance layer does not care who wrote it.
"""

from __future__ import annotations

import os
import re

# ---------------------------------------------------------------------------
# Readability
# ---------------------------------------------------------------------------

_ACTION_VERBS = {
    "add", "ask", "assign", "check", "choose", "click", "contact", "enter",
    "fill", "fix", "leave", "lower", "open", "pick", "raise", "remove",
    "reply", "review", "select", "send", "set", "submit", "tell", "try",
    "update", "use", "write",
}

# Language that describes the system's state instead of the reader's next move.
_JARGON = [
    "invalid", "illegal", "error:", "failed", "failure", "must be populated",
    "requisite", "hereby", "referenced", "subject record", "disposition",
    "remediation", "deficient", "consult", "aforementioned", "pursuant",
    "exception report", "value required", "prior to proceeding", "determined to be",
]


def _normalise(text: str) -> str:
    """Make symbols and numerals speakable before we count syllables."""
    text = text.replace("%", " percent").replace("$", " dollars ")
    text = text.replace("&", " and ")
    return text


def _syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    groups = re.findall(r"[aeiouy]{1,2}", w)
    return max(1, len(groups))


def _token_syllables(token: str) -> int:
    """Digits are spoken roughly one syllable per digit: 20 -> twen-ty."""
    digits = re.sub(r"[^0-9]", "", token)
    if digits and not re.search(r"[a-zA-Z]", token):
        return max(1, len(digits))
    return _syllables(token)


def readability(text: str) -> dict:
    """Flesch-Kincaid grade level and Flesch reading ease.

    Grade level is the US school grade needed to read the text on one pass.
    Salesforce's own content guidance, and WCAG 3.1.5, both point at roughly
    grade 8 for interface copy.
    """
    clean = _normalise(text.strip())
    sentences = [s for s in re.split(r"[.!?]+", clean) if s.strip()]
    words = re.findall(r"[A-Za-z0-9']+", clean)
    if not words or not sentences:
        return {"grade": 0.0, "ease": 100.0, "words": 0, "sentences": 0, "wps": 0.0}

    syl = sum(_token_syllables(w) for w in words)
    wps = len(words) / len(sentences)
    spw = syl / len(words)
    grade = 0.39 * wps + 11.8 * spw - 15.59
    ease = 206.835 - 1.015 * wps - 84.6 * spw
    return {
        "grade": round(max(0.0, grade), 1),
        "ease": round(ease, 1),
        "words": len(words),
        "sentences": len(sentences),
        "wps": round(wps, 1),
    }


def is_actionable(text: str) -> tuple[bool, str]:
    """Does the message tell the reader what to do next?"""
    for clause in re.split(r"[.,;]", text):
        first = re.findall(r"[A-Za-z']+", clause.strip())
        if first and first[0].lower() in _ACTION_VERBS:
            return True, first[0].lower()
    return False, ""


def jargon_hits(text: str) -> list[str]:
    low = text.lower()
    return [j for j in _JARGON if j in low]


# ---------------------------------------------------------------------------
# Artifact parsing - the checks read the drafted config, not a fixture
# ---------------------------------------------------------------------------

_INPUT_TYPES = ("picklist", "text", "text area", "number", "date", "currency", "email", "phone")

# Salesforce field types, so a type group cannot swallow an adjacent config line.
_FIELD_TYPES = (r"(?:Checkbox|Picklist|Text Area|Text|Number|Date(?:/Time)?|Currency"
                r"|Email|Phone|Percent|Formula|Lookup|Long Text Area)")

# Abbreviations a screen reader mangles or reads as a different word.
_BAD_ABBR = {
    "disc": "reads as \"disk\"", "opp": "reads as \"op\"", "qty": "spelled out letter by letter",
    "mgr": "spelled out letter by letter", "amt": "spelled out letter by letter",
    "pct": "spelled out letter by letter", "cust": "reads as \"cust\"",
    "acct": "spelled out letter by letter", "rev": "reads as \"rev\"",
}


def parse_artifact(code: str) -> dict:
    """Pull the accessibility-relevant facts out of a drafted artifact."""
    out = {"error_location": None, "labels": [], "help_texts": [], "fields": []}

    m = re.search(r"Error Location\s+(\S+)", code)
    if m:
        out["error_location"] = m.group(1)

    for m in re.finditer(r"^\s*Label\s{2,}(.+)$", code, re.M):
        out["labels"].append(m.group(1).strip())

    out["help_texts"] = re.findall(r"Help Text\s{2,}(.+)", code)

    # Field declarations look like  Name__c · Type · ...  or  Field  Name__c
    # The separator must sit on the same line: an approval process lists
    # "Field Update  Approved_Date__c" followed by a bulleted next action, and
    # a newline-crossing match reads that next action as the field's type.
    for m in re.finditer(rf"([A-Za-z_]+__c)[^\S\n]*·[^\S\n]*({_FIELD_TYPES}[^·\n]*)", code):
        out["fields"].append((m.group(1), m.group(2).strip()))
    for m in re.finditer(r"^(?:Field|New field)\s{2,}([A-Za-z_]+__c)", code, re.M):
        if not any(f[0] == m.group(1) for f in out["fields"]):
            tm = re.search(rf"{re.escape(m.group(1))}[\s\S]{{0,120}}?^Type\s{{2,}}(.+)$", code, re.M)
            out["fields"].append((m.group(1), tm.group(1).strip() if tm else "Unknown"))
    return out


def accessibility_audit(option: dict, message: str) -> list[dict]:
    """Six checks over the artifact Clearance just drafted.

    Each returns status pass / fail / n-a, plus the evidence it used, so a
    reviewer can argue with the finding instead of trusting it.
    """
    code = option["code"]
    facts = parse_artifact(code)
    checks: list[dict] = []

    # 1. Reading level
    r = readability(message)
    checks.append({
        "name": "Reads at grade 8 or below",
        "why": "WCAG 3.1.5. Interface copy that needs a college reading level excludes people under stress, in a second language, or with a cognitive disability.",
        "status": "pass" if r["grade"] <= 8 else "fail",
        "evidence": f"Flesch-Kincaid grade {r['grade']} · {r['words']} words in {r['sentences']} sentence(s) · {r['wps']} words per sentence",
    })

    # 2. Actionable
    ok, verb = is_actionable(message)
    checks.append({
        "name": "Tells the reader what to do",
        "why": "A message that only names the problem leaves the reader stuck. Screen reader users hear it once, out of visual context, with no layout to infer from.",
        "status": "pass" if ok else "fail",
        "evidence": f'Opens a clause with the instruction "{verb}"' if ok
                    else "No instruction found. The message describes a state, not a next step.",
    })

    # 3. Blame / system jargon
    hits = jargon_hits(message)
    checks.append({
        "name": "No system jargon or blame language",
        "why": "\"Invalid entry\" describes the database's opinion of the user. Plain language describes the fix.",
        "status": "pass" if not hits else "fail",
        "evidence": "Clean." if not hits else "Found: " + ", ".join(f'"{h}"' for h in hits),
    })

    # 4. Error bound to the field
    loc = facts["error_location"]
    if loc is None:
        checks.append({
            "name": "Error is bound to its field",
            "why": "An error set to Top of Page is announced with no programmatic link to the input that caused it, so a screen reader user cannot find it.",
            "status": "n-a",
            "evidence": "This artifact raises no inline field error.",
        })
    else:
        good = "top" not in loc.lower()
        checks.append({
            "name": "Error is bound to its field",
            "why": "An error set to Top of Page is announced with no programmatic link to the input that caused it, so a screen reader user cannot find it.",
            "status": "pass" if good else "fail",
            "evidence": f"Error Location = {loc}",
        })

    # 5. Help text on fields people type into
    typed = [f for f in facts["fields"] if any(t in f[1].lower() for t in _INPUT_TYPES)]
    if not typed:
        auto = ", ".join(f[0] for f in facts["fields"]) or "none"
        checks.append({
            "name": "User-entered fields carry help text",
            "why": "Screen reader users cannot infer a field's purpose from where it sits on the layout. Help text is the only description they get.",
            "status": "n-a",
            "evidence": f"No user-entered fields in this draft. Automation checkpoints ({auto}) stay off the page layout.",
        })
    else:
        enough = len(facts["help_texts"]) >= len(typed)
        checks.append({
            "name": "User-entered fields carry help text",
            "why": "Screen reader users cannot infer a field's purpose from where it sits on the layout. Help text is the only description they get.",
            "status": "pass" if enough else "fail",
            "evidence": f"{len(typed)} field(s) people type into · {len(facts['help_texts'])} help text block(s) written",
        })

    # 6. Labels that survive being read aloud
    flagged = []
    for lab in facts["labels"]:
        for abbr, effect in _BAD_ABBR.items():
            if re.search(rf"\b{abbr}\b", lab.lower()):
                flagged.append(f'"{lab}" - "{abbr}" {effect}')
    if not facts["labels"]:
        checks.append({
            "name": "Labels survive being read aloud",
            "why": "Abbreviations a sighted user decodes from context become noise in a screen reader.",
            "status": "n-a",
            "evidence": "This artifact defines no new field labels.",
        })
    else:
        checks.append({
            "name": "Labels survive being read aloud",
            "why": "Abbreviations a sighted user decodes from context become noise in a screen reader.",
            "status": "pass" if not flagged else "fail",
            "evidence": (", ".join(f'"{l}"' for l in facts["labels"]) + " - all spelled out")
                        if not flagged else "; ".join(flagged),
        })

    return checks


def audit_score(checks: list[dict]) -> tuple[int, int]:
    """(passed, applicable) - n-a checks are excluded from the denominator."""
    live = [c for c in checks if c["status"] != "n-a"]
    return sum(1 for c in live if c["status"] == "pass"), len(live)


# ---------------------------------------------------------------------------
# Classification for free-text requests
# ---------------------------------------------------------------------------

_ROUTES = [
    ("Approval Process", 0.0, ["approv", "sign-off", "sign off", "authorise", "authorize", "vp needs", "before it can"]),
    ("Validation Rule", 0.0, ["stop", "prevent", "block", "warn", "not allowed",
                              "shouldn't", "should not", "nobody should", "no one should",
                              "can't close", "cannot close", "unless", "require", "must "]),
    ("Schedule-Triggered Flow", 0.0, ["every day", "daily", "weekly", "remind", "notify", "alert", "when a", "automatically", "days before", "months out"]),
    ("Custom Field + Report", 0.0, ["track", "capture", "field for", "record why", "store", "somewhere to put"]),
    ("Report", 0.0, ["report", "dashboard", "show me", "chart", "how many", "breakdown"]),
]


def classify(text: str) -> dict:
    """Keyword routing for a free-typed request.

    Honest about what it is: lexical, not semantic. With a real key set it is
    replaced by a model call — and the checks downstream are identical either
    way, which is the architectural claim this demo is making.
    """
    low = text.lower()
    scored = []
    for artifact, _, keys in _ROUTES:
        hits = [k for k in keys if k in low]
        if hits:
            scored.append((len(hits), artifact, hits))
    if not scored:
        return {"artifact": "Needs a human", "confidence": 0.0, "hits": [],
                "obj": "Unknown", "routed": True}
    scored.sort(reverse=True)
    hits, artifact, matched = scored[0]
    obj = "Opportunity"
    if "account" in low or "customer" in low or "churn" in low:
        obj = "Account"
    if "case" in low or "ticket" in low or "support" in low:
        obj = "Case"
    if "contact" in low or "lead" in low:
        obj = "Lead"
    return {"artifact": artifact, "confidence": min(0.62 + 0.11 * hits, 0.93),
            "hits": matched, "obj": obj, "routed": False}


# ---------------------------------------------------------------------------
# Optional real model
# ---------------------------------------------------------------------------

def llm_available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def llm_draft(request_text: str, org_summary: str) -> str | None:
    """Draft an artifact with a real model. Returns None if unavailable."""
    if not llm_available():
        return None
    try:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1200,
            system=(
                "You are Clearance, a Salesforce change-request drafting assistant. "
                "Given a business user's plain-English request, draft the declarative "
                "Salesforce artifact that satisfies it: validation rule, flow, custom "
                "field, approval process, or report. Output the config as a plain-text "
                "spec in the same shape a Salesforce admin would read in Setup. "
                "Write any user-facing error or notification text at a grade 8 reading "
                "level, tell the reader what to do, and bind errors to a field rather "
                "than the page. Never output Apex. Never claim the change is deployed."
            ),
            messages=[{"role": "user",
                       "content": f"Org context:\n{org_summary}\n\nRequest:\n{request_text}"}],
        )
        return msg.content[0].text
    except Exception as exc:  # surfaced in the UI, never swallowed
        return f"__ERROR__{exc}"
