# Clearance

**A governed intake-to-change pipeline for Salesforce.**
Business request in. Reviewable Salesforce change out.

A concept demo built for an application to the Salesforce Associate Product
Manager programme. Not affiliated with Salesforce. Nothing here contacts a
live org.

---

## The problem

A sales ops manager needs a rule changed. She cannot change it — no Setup
access, no Flow Builder, no business writing formula syntax. So she files a
ticket, and it joins 87 others behind 3 admins serving 340 users. Median time
to get anything live: 19 days, for changes that take twenty minutes to build.

Roughly 40% of that queue never needed an admin at all. It is duplicates, and
things the org can already do that nobody knew how to find.

## What Clearance does

Six screens, one request, start to finish:

1. **Ask** — a business user describes what they need in plain English.
2. **Draft** — Clearance classifies it, restates it, and **asks the one
   question a ticket queue never asks** before drafting the real Salesforce
   artifact (validation rule, flow, field, approval process).
3. **Impact** — objects touched, records in scope, governor limits, conflicts
   with existing automation, and the blast radius nobody finds until after the
   build.
4. **Accessibility gate** — six checks over the drafted artifact and the text
   it puts in front of a human.
5. **Admin review** — a ranked queue, a plain-English summary, one click.
6. **What changed** — the impact view, plus the product reasoning.

**Clearance drafts, analyses and checks. It cannot deploy.** An AI with write
access to production metadata is a trust problem dressed as a convenience.
Keeping a human on the deploy is what makes the speed safe to accept.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

No API key needed. The engine is deterministic by default so the demo never
fails in front of anyone.

**Optional live model.** Set `ANTHROPIC_API_KEY` and install `anthropic`, and a
real model drafts instead. The same accessibility gate runs over its output —
the governance layer does not care who wrote the draft, which is the
architectural point.

## Sharing this with someone

The demo is most useful as a link. Streamlit Community Cloud hosts it free:

1. Push this folder to a public GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. Point it at the repo, set the main file to `app.py`, deploy.

It picks up `requirements.txt` on its own. No key or secret is needed — the
deterministic engine is the default, which is exactly why it is the default.

## What is actually computed

The line between real and staged matters, so it is drawn explicitly:

| Genuinely computed | Staged |
|---|---|
| Flesch-Kincaid grade level, syllable counting included | The org, its users, and its backlog |
| Artifact parsing — error binding, field types, help text, labels | The four request scenarios |
| All six accessibility checks, live over on-screen text | The before/after metrics (modelled, not measured) |
| Free-text classification (lexical, and it says so on screen) | |

The accessibility checks will fail copy written in this repo. That is how you
know they are measuring something rather than decorating it.

## Files

| File | What is in it |
|---|---|
| `app.py` | The six screens and the router |
| `engine.py` | Readability, artifact parsing, the six checks, optional model call |
| `catalog.py` | The seeded org and the four worked requests |
| `charts.py` | The two impact charts |
| `theme.py` | Salesforce Lightning Design System tokens and CSS |

## Notes on the build

**The palette was validated, not eyeballed.** The first two-series pair
(blue `#0176D3` + violet `#9050E9`) failed colour-vision separation at ΔE 3.3
for deuteranopes — two lines a large minority of readers could not tell apart.
It was dropped for the emphasis pattern: one series in brand blue carries the
story, the baseline recedes to grey.

**This app holds itself to the line it argues for.** Status never depends on
colour alone. Every chart has a table view. Focus outlines are visible. The
progress path carries its state in text, not just in fill.
