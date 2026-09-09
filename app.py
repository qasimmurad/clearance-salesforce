"""Clearance - a governed intake-to-change pipeline for Salesforce.

A click-through demo: one screen at a time, from a business user's plain-English
request to an admin's one-click approval, with an impact analysis and an
accessibility gate in between.

Run:  streamlit run app.py
"""

from __future__ import annotations

import warnings

import streamlit as st

warnings.filterwarnings("ignore", category=FutureWarning)

import catalog  # noqa: E402
import charts  # noqa: E402
import engine  # noqa: E402
import theme as T  # noqa: E402

STEPS = ["The problem", "Ask", "Draft", "Impact",
         "Accessibility", "Admin review", "What changed"]

st.set_page_config(page_title="Clearance · Salesforce change requests",
                   page_icon="◆", layout="centered",
                   initial_sidebar_state="collapsed")
st.markdown(T.CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# state
# ---------------------------------------------------------------------------
def _init():
    d = {"step": 0, "req": 0, "opt": None, "decision": None,
         "typed": "", "classified": None}
    for k, v in d.items():
        st.session_state.setdefault(k, v)


_init()
S = st.session_state


def goto(n: int):
    S.step = max(0, min(n, len(STEPS) - 1))
    st.rerun()


def request():
    return catalog.REQUESTS[S.req]


def option():
    r = request()
    key = S.opt or r["options"][0]["key"]
    return next(o for o in r["options"] if o["key"] == key)


def md(html: str):
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# chrome
# ---------------------------------------------------------------------------
def masthead():
    md(f"""
    <div class="cl-masthead">
      <div class="cl-mark" aria-hidden="true">CL</div>
      <div>
        <h1>Clearance</h1>
        <p>Business request in. Governed Salesforce change out.</p>
      </div>
      <div class="cl-org">
        <b>{catalog.ORG['name']}</b> · {catalog.ORG['edition']}<br>
        {catalog.ORG['users']} users · {catalog.ORG['admins']} admins ·
        {catalog.ORG['open_requests']} open requests
      </div>
    </div>""")


def path():
    cells = []
    for i, name in enumerate(STEPS):
        cls = "now" if i == S.step else ("done" if i < S.step else "")
        state = "current step" if i == S.step else ("done" if i < S.step else "not started")
        cells.append(
            f'<div class="cl-step {cls}" role="listitem" aria-current='
            f'"{"step" if i == S.step else "false"}">{i + 1}. {name}'
            f'<span class="cl-sr"> — {state}</span></div>')
    md(f'<div class="cl-path" role="list" aria-label="Progress through the request">'
       f'{"".join(cells)}</div>')


def nav(back: bool = True, forward: str | None = None, target: int | None = None):
    st.write("")
    c1, c2 = st.columns([1, 1])
    with c1:
        if back and S.step > 0 and st.button("← Back", key=f"b{S.step}", use_container_width=True):
            goto(S.step - 1)
    with c2:
        if forward and st.button(forward, key=f"f{S.step}", type="primary",
                                 use_container_width=True):
            goto(S.step + 1 if target is None else target)


# ---------------------------------------------------------------------------
# 0 · the problem
# ---------------------------------------------------------------------------
def screen_problem():
    md("## The bottleneck this is aimed at")
    md(f"""
    <div class="cl-card">
      <p class="cl-eyebrow">The shape of the problem</p>
      <p>A sales ops manager needs a rule changed. She cannot change it. She has no
      Setup access, no Flow Builder, and no business writing formula syntax. So she
      files a ticket, and it joins
      <b>{catalog.ORG['open_requests']} others</b> behind
      <b>{catalog.ORG['admins']} admins</b> serving
      <b>{catalog.ORG['users']} users</b>. Median time to get anything live:
      <b>{catalog.ORG['median_age_days']} days</b>.</p>
    </div>""")

    a, b, c = st.columns(3)
    with a:
        md(T.tile("Requests one admin is holding", "29", "87 open, 3 admins"))
    with b:
        md(T.tile("Median wait, request to live", "19 days", "for a 20-minute change"))
    with c:
        md(T.tile("Abandoned before anyone builds it", "22%", "the request just dies"))

    md(T.note(
        "Roughly a third of that queue never needed an admin at all. It is duplicates, "
        "and things the org can already do that nobody knew how to find. The rest is "
        "real work — but the drafting is mechanical, and the judgement is not. "
        "<b>Clearance splits those two apart:</b> it drafts, analyses and checks; "
        "a human decides.",
        "The insight", "brand"))

    md(f"""
    <div class="cl-card">
      <p class="cl-eyebrow">What you are about to click through</p>
      <p>You will play a sales ops manager with no admin rights, describe something you
      need in plain English, and watch it become a reviewable Salesforce change —
      through an impact analysis and an accessibility gate — in six screens.
      Nothing here touches a live org. The engine runs deterministically so this
      demo never fails in front of you.</p>
    </div>""")

    nav(back=False, forward="Start →")


# ---------------------------------------------------------------------------
# 1 · ask
# ---------------------------------------------------------------------------
def screen_ask():
    md("## What do you need?")
    md(f"""
    <div class="cl-card">
      <p class="cl-eyebrow">You are</p>
      <h3>{catalog.PERSONA['name']} · {catalog.PERSONA['title']}</h3>
      <p>{catalog.PERSONA['access']}</p>
    </div>""")

    md('<p class="cl-eyebrow" style="margin-top:14px">Pick something real people ask for</p>')

    cols = st.columns(2)
    for i, r in enumerate(catalog.REQUESTS):
        with cols[i % 2]:
            if st.button(f"**{r['bubble']}**\n\n{r['bubble_sub']}",
                         key=f"bub{i}", use_container_width=True):
                S.req, S.opt, S.decision = i, None, None
                S.typed, S.classified = "", None
                goto(2)

    st.write("")
    with st.expander("Or type your own request"):
        typed = st.text_area(
            "Describe what you need, the way you would say it out loud",
            placeholder="e.g. Nobody should be able to close a deal without a signed order form attached.",
            height=90, key="ta")
        if st.button("Send it to Clearance", key="send") and typed.strip():
            S.typed = typed.strip()
            S.classified = engine.classify(typed)
            match = next((i for i, r in enumerate(catalog.REQUESTS)
                          if r["artifact"] == S.classified["artifact"]), 0)
            S.req, S.opt, S.decision = match, None, None
            goto(2)

    nav(forward=None)


# ---------------------------------------------------------------------------
# 2 · draft
# ---------------------------------------------------------------------------
def screen_draft():
    r = request()
    md("## What Clearance read, and what it refuses to guess")

    if S.typed and S.classified:
        cl = S.classified
        hits = ", ".join(f'"{h}"' for h in cl["hits"]) or "no strong signal"
        if cl["routed"]:
            body = (f'You typed: <em>"{S.typed}"</em><br><br>'
                    f'The deterministic engine found no confident match, so it says so '
                    f'rather than guessing — a request it cannot read goes to a human '
                    f'with the text intact, which is the correct failure mode for this '
                    f'product. To keep walking the flow, it will use the closest worked '
                    f'example, <b>{r["id"]}</b>.')
        else:
            body = (f'You typed: <em>"{S.typed}"</em><br><br>'
                    f'The deterministic engine classified that as <b>{cl["artifact"]}</b> '
                    f'on <b>{cl["obj"]}</b> from a lexical match on {hits}. That is '
                    f'keyword routing, not comprehension, and this build says so rather '
                    f'than dressing it up. The four seeded requests are worked end to '
                    f'end — continuing with the closest one, <b>{r["id"]}</b>.')
        md(T.note(body, "Your own request", "warn"))
        if engine.llm_available():
            md(T.note("An API key is set, so a real model can draft this one instead. "
                      "Open the drafting panel at the bottom of this screen.",
                      "Live model available", "good"))

    md(f"""
    <div class="cl-card">
      <p class="cl-eyebrow">{r['id']} · submitted by {catalog.PERSONA['name']}</p>
      <p style="font-size:14.5px;color:{T.INK};font-style:italic">"{r['raw']}"</p>
    </div>""")

    md(T.chip(r["artifact"], "brand", "◆")
       + T.chip(f"Object: {r['obj']}", "neutral")
       + T.chip(f"Classifier confidence {int(r['confidence'] * 100)}%", "neutral"))

    md(f"""
    <div class="cl-card">
      <p class="cl-eyebrow">Clearance restates it back</p>
      <p style="color:{T.INK};font-size:14.5px">{r['restatement']}</p>
    </div>""")

    # --- the ambiguity it will not guess at -------------------------------
    md(T.note(r["clarify_why"], "Before anything is drafted", "warn"))
    md(f'<h3 style="font-size:15.5px;margin:14px 0 2px">{r["clarify_q"]}</h3>')

    labels = [f'{o["label"]} — {o["meta"]}' for o in r["options"]]
    keys = [o["key"] for o in r["options"]]
    idx = keys.index(S.opt) if S.opt in keys else 0
    pick = st.radio("Choose how this should behave", labels, index=idx,
                    key=f"opt{S.req}", label_visibility="collapsed")
    S.opt = keys[labels.index(pick)]

    o = option()
    tone = {"Low": "good", "Medium": "warn", "High": "critical"}[o["risk"]]
    md(f'<p class="cl-eyebrow" style="margin-top:16px">The draft · '
       f'{o["label"]}</p>' + T.chip(f"Risk: {o['risk']}", tone, "▲"))
    st.code(o["code"], language="text")

    md(T.note(
        "This is a <b>proposal</b>. Nothing is deployed, nothing is scheduled, and no "
        "metadata has been written. The next two screens are what a reviewer needs "
        "before they are allowed to say yes.",
        "Not deployed", "brand"))

    if engine.llm_available():
        with st.expander("Draft this with a live model instead"):
            if st.button("Call the model", key="llm"):
                with st.spinner("Drafting…"):
                    out = engine.llm_draft(
                        S.typed or r["raw"],
                        f"{catalog.ORG['name']}, {catalog.ORG['edition']}, "
                        f"{catalog.ORG['users']} users, {catalog.ORG['opp_custom_fields']} "
                        f"custom fields on Opportunity, {catalog.ORG['active_flows']} active flows.")
                if out and out.startswith("__ERROR__"):
                    st.error(f"Model call failed: {out[9:]}")
                elif out:
                    st.code(out, language="text")
                    st.caption("The same accessibility gate runs over this output. "
                               "The governance layer does not care who wrote the draft.")

    nav(forward="See what this would do →")


# ---------------------------------------------------------------------------
# 3 · impact
# ---------------------------------------------------------------------------
def screen_impact():
    r, o = request(), option()
    md("## What this would actually do to the org")

    md(T.note(f"<span class='lead'>{r['blast']['headline']}</span>"
              f"{r['blast']['body']}",
              "Blast radius", r["blast"]["tone"]))

    imp = r["impact"]
    md('<div class="cl-card"><p class="cl-eyebrow">Impact analysis</p>'
       + T.row("Objects touched", imp["objects"])
       + T.row("Records in scope", imp["in_scope"])
       + T.row("Governor limits", imp["limits"])
       + T.row("Rollback", imp["rollback"])
       + "</div>")

    md(T.note(imp["conflicts"], "Conflicts with what is already there", "warn"))

    tone = {"Low": "good", "Medium": "warn", "High": "critical"}[o["risk"]]
    md('<div class="cl-card"><p class="cl-eyebrow">Reviewer summary</p>'
       + f'<p>{o["label"]} · {o["meta"]}</p><div style="margin-top:8px">'
       + T.chip(f"Risk: {o['risk']}", tone, "▲")
       + T.chip("Reversible", "good", "✓") + "</div></div>")

    md(T.note(
        "None of this is the clever part. The clever part is that it happens "
        "<em>before</em> an admin spends an afternoon building the thing — which is "
        "when the 41-records-already-broken problem normally gets discovered.",
        "", "brand"))

    nav(forward="Run the accessibility gate →")


# ---------------------------------------------------------------------------
# 4 · accessibility gate
# ---------------------------------------------------------------------------
def _msg_card(title, text, grade, tone):
    md(f"""
    <div class="cl-card" style="border-left:4px solid {tone}">
      <p class="cl-eyebrow">{title}</p>
      <p style="color:{T.INK};font-size:14px">"{text}"</p>
      <p style="margin-top:8px;font-size:12px;color:{T.INK_SOFT}">
        Flesch-Kincaid grade {grade['grade']} · {grade['words']} words ·
        {grade['wps']} words per sentence</p>
    </div>""")


def screen_a11y():
    o = option()
    md("## The accessibility gate")
    md(T.note(
        "Every change Clearance drafts writes text a human has to read — an error "
        "message, an email, a field label. That text is where Salesforce becomes "
        "usable or unusable for someone with a cognitive disability, someone reading "
        "in a second language, or someone hearing it through a screen reader with no "
        "layout to infer from. So it gets checked before a reviewer ever sees it, "
        "not after a customer complains.",
        "Why this screen exists at all", "brand"))

    draft_r = engine.readability(o["msg_draft"])
    rev_r = engine.readability(o["msg_revised"])

    md('<p class="cl-eyebrow" style="margin-top:14px">The message a typical ticket produces</p>')
    _msg_card("Before", o["msg_draft"], draft_r, T.CRITICAL)
    md('<p class="cl-eyebrow">Clearance rewrites it</p>')
    _msg_card("After", o["msg_revised"], rev_r, T.SUCCESS)

    drop = round(draft_r["grade"] - rev_r["grade"], 1)
    if drop > 0:
        md(T.note(f"Reading level dropped <b>{drop} grades</b>, from "
                  f"{draft_r['grade']} to {rev_r['grade']}. Same rule, same "
                  f"behaviour, same enforcement — a reader who can act on it.",
                  "", "good"))

    md('<p class="cl-eyebrow" style="margin-top:18px">Six checks, run over the drafted artifact</p>')
    checks = engine.accessibility_audit(o, o["msg_revised"])
    for c in checks:
        tone, word, icon = {"pass": ("good", "Pass", "✓"),
                            "fail": ("critical", "Fail", "✕"),
                            "n-a": ("neutral", "Not applicable", "–")}[c["status"]]
        md(f'<div class="cl-card"><div style="display:flex;gap:10px;align-items:flex-start">'
           f'<div style="flex:0 0 auto">{T.chip(word, tone, icon)}</div>'
           f'<div><h3 style="font-size:14px;margin:2px 0 4px">{c["name"]}</h3>'
           f'<p style="font-size:12.5px">{c["why"]}</p>'
           f'<p style="font-size:12.5px;margin-top:6px;color:{T.INK}">'
           f'<b>Evidence:</b> {c["evidence"]}</p></div></div></div>')

    p, n = engine.audit_score(checks)
    dp, dn = engine.audit_score(engine.accessibility_audit(o, o["msg_draft"]))
    md(T.note(
        f"The rewritten artifact passes <b>{p} of {n}</b> applicable checks. "
        f"The original wording passed <b>{dp} of {dn}</b>. These are computed live "
        f"over the text on this screen — the grade levels above are a real "
        f"Flesch-Kincaid calculation, not a stored number, and the checks will fail "
        f"copy this repo wrote itself.",
        "Result", "good"))

    nav(forward="Send to an admin →")


# ---------------------------------------------------------------------------
# 5 · admin review
# ---------------------------------------------------------------------------
def screen_review():
    r, o = request(), option()
    md("## The admin's queue")
    md(f"""
    <div class="cl-card">
      <p class="cl-eyebrow">Signed in as</p>
      <h3>Marcus Reed · Salesforce Administrator</h3>
      <p>One of three admins. Queue is ranked by what is ready to decide, not by
      what arrived first.</p>
    </div>""")

    tone = {"Low": "good", "Medium": "warn", "High": "critical"}[o["risk"]]
    md(f"""
    <div class="cl-card" style="border-left:4px solid {T.BRAND}">
      <p class="cl-eyebrow">1 · Drafted and checked · waiting on you</p>
      <h3>{r['id']} — {r['bubble']}</h3>
      <p style="margin:6px 0 10px">{r['restatement']}</p>
      <div>{T.chip(r['artifact'], 'brand', '◆')}{T.chip(o['label'], 'neutral')}
      {T.chip(f"Risk: {o['risk']}", tone, '▲')}
      {T.chip('Accessibility gate passed', 'good', '✓')}</div>
    </div>""")

    st.caption("Behind it, the rest of the queue as Clearance has triaged it:")
    # REQ-1044 is both a seeded queue row and one of the four things a user can
    # ask for. Whichever one is on the desk now must not also appear below it.
    for rid, title, kind, age, status in catalog.QUEUE:
        if rid == r["id"]:
            continue
        t = ("good" if status in ("Answered", "Closed as duplicate")
             else "warn" if status == "With admin" else "neutral")
        md(f'<div class="cl-row"><span class="k"><b>{rid}</b> · {title}<br>'
           f'<span style="font-size:11.5px">{kind} · {age} days old</span></span>'
           f'<span class="v">{T.chip(status, t)}</span></div>')

    st.write("")
    md('<p class="cl-eyebrow">Your call</p>')
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Approve and schedule", type="primary", use_container_width=True):
            S.decision = "approved"
    with c2:
        if st.button("Send back a question", use_container_width=True):
            S.decision = "returned"
    with c3:
        if st.button("Decline", use_container_width=True):
            S.decision = "declined"

    if S.decision:
        body = {
            "approved": ("good", "Queued for the next deployment window. Clearance "
                         "writes the audit entry, attaches the impact analysis and "
                         "the accessibility findings to the change record, and tells "
                         f"{catalog.PERSONA['name']} it is coming."),
            "returned": ("warn", f"{catalog.PERSONA['name']} gets your question with "
                         "the draft attached, so she is answering about something "
                         "concrete rather than re-explaining from scratch."),
            "declined": ("critical", "Declined with a reason on the record. The draft "
                         "and the analysis stay attached, so the next person who asks "
                         "for this sees why it was turned down."),
        }[S.decision]
        md(T.note(
            f"{body[1]}<br><br>"
            f"<code style='font-size:11.5px'>AUDIT · {r['id']} · {S.decision.upper()} · "
            f"M. Reed · drafted by Clearance · reviewed by a human · "
            f"impact + accessibility findings attached</code>",
            f"Decision recorded: {S.decision}", body[0]))
        md(T.note(
            "This is the product decision the whole thing rests on. Clearance can "
            "draft, analyse and check — and it still cannot ship. An AI that writes "
            "directly to a production org is a trust problem dressed as a "
            "convenience. Keeping a human on the deploy is what makes the speed "
            "safe to accept.",
            "Why there is no auto-deploy", "brand"))
        nav(forward="See what changes at scale →")
    else:
        nav(forward=None)


# ---------------------------------------------------------------------------
# 6 · what changed
# ---------------------------------------------------------------------------
def screen_impact_dash():
    md("## What changes when the whole queue works this way")

    md(f"""
    <div class="cl-hero">
      <div class="fig">2.3 days</div>
      <div class="cap">Modelled median time from request to live, down from
      {catalog.ORG['median_age_days']} days. The change is not that admins get
      faster — it is that a third of the queue stops reaching them, and the rest
      arrives already drafted, analysed and checked.</div>
    </div>""")

    cols = st.columns(4)
    for col, (lab, val, was) in zip(cols, catalog.METRICS):
        with col:
            md(T.tile(lab, val, was))

    st.write("")
    md('<div class="cl-card"><p class="cl-eyebrow">Open request backlog, 12 weeks</p>'
       '<p>Same three admins, same inflow. The difference is what reaches them.</p></div>')
    st.altair_chart(charts.backlog_chart(), use_container_width=True)
    with st.expander("View as table"):
        st.dataframe(charts.backlog_table(), use_container_width=True)

    md('<div class="cl-card"><p class="cl-eyebrow">Where the 87 open requests go</p>'
       '<p>Triaged by Clearance before an admin opens anything.</p></div>')
    st.altair_chart(charts.triage_chart(), use_container_width=True)
    with st.expander("View as table"):
        st.dataframe(charts.triage_table(), use_container_width=True)

    md(T.note(
        "<span class='lead'>35 of 87 requests never needed an admin.</span>"
        "24 were already possible and nobody knew where to "
        "look; 11 were duplicates of something already in flight. That is 40% of a "
        "queue that exists because the org has no way to answer a question without "
        "opening a ticket.",
        "The finding under the chart", "brand"))

    # ---- product notes -------------------------------------------------
    st.write("")
    md("### Product notes")

    with st.expander("What I would measure, and what would tell me I was wrong"):
        md(f"""
        <p style="font-size:13.5px;line-height:1.65">
        <b>North star:</b> requests fulfilled per admin per month. It moves only if
        both halves work — deflection <em>and</em> drafting — and it cannot be gamed
        by closing tickets faster.<br><br>
        <b>Guardrail metrics,</b> because the failure mode of this product is
        shipping bad changes quickly:<br>
        · rollback rate on Clearance-drafted changes vs. hand-built ones. If drafted
        changes get reverted more often, the drafting is not good enough and the
        speed is a liability.<br>
        · share of approvals taking under 30 seconds. Rubber-stamping means the
        review is theatre and the trust story is false.<br>
        · requests where the clarifying question changed the answer. That is the
        single number that says the AI is doing product work rather than
        transcription.<br><br>
        <b>What would kill it:</b> if admins do not trust the impact analysis, they
        rebuild from scratch and Clearance is a slower ticket form. I would ship to
        three friendly admins and watch whether they read the analysis or scroll
        past it.</p>""")

    with st.expander("What I cut, and why"):
        md("""
        <p style="font-size:13.5px;line-height:1.65">
        <b>Auto-deploy.</b> The demo is faster with it and the product is worse.
        Salesforce sells trust before it sells automation; an agent with write access
        to production metadata is a headline waiting to happen.<br><br>
        <b>Apex generation.</b> Roughly 8 of 87 requests need code. Generating Apex
        means generating tests, coverage and a deployment story — a different product.
        Clearance routes those out with the spec attached, which is worth more than a
        bad attempt.<br><br>
        <b>A chat interface.</b> The request is a form with one good question in it.
        A chat window would hide the impact analysis behind a scroll, and the
        analysis is the product.</p>""")

    with st.expander("Where accessibility actually sits in this"):
        md("""
        <p style="font-size:13.5px;line-height:1.65">
        Not as a compliance checkbox at the end. Every change to a CRM writes text a
        human reads under pressure, and the ticket queue is the worst possible place
        for that text to be authored — it gets written by whoever is closing the
        ticket, at the end of an afternoon, with no reader in mind. Putting the check
        at the point of drafting is the only place it is cheap.<br><br>
        The gate on the earlier screen is real: Flesch-Kincaid computed live, the
        artifact parsed for its error binding and help text, labels scanned for
        abbreviations a screen reader mangles. It fails copy written in this repo,
        which is the only way to know it is measuring something.<br><br>
        This app holds itself to the same line: status never depends on colour alone,
        every chart has a table view, focus outlines are visible, and the two-series
        palette was rejected and re-picked after a validator showed
        blue-versus-violet at Delta-E 3.3 for deuteranopes.</p>""")

    md(T.note(
        "The org is invented. The metrics are modelled from published admin-to-user "
        "ratios and this org's own trailing averages — they are a hypothesis about "
        "what would happen, not a measurement of what did. Nothing connects to a "
        "Salesforce instance. The classifier on the free-text path is keyword "
        "matching and says so on screen. The accessibility scoring and artifact "
        "parsing are the parts that are genuinely computed.",
        "What this demo is not", "warn"))

    st.write("")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("← Back", use_container_width=True):
            goto(5)
    with c2:
        if st.button("Run another request", type="primary", use_container_width=True):
            S.opt = S.decision = S.classified = None
            S.typed = ""
            goto(1)


# ---------------------------------------------------------------------------
SCREENS = [screen_problem, screen_ask, screen_draft, screen_impact,
           screen_a11y, screen_review, screen_impact_dash]

masthead()
path()
SCREENS[S.step]()

st.write("")
st.caption("Clearance · a concept demo for the Salesforce Associate Product Manager "
           "programme. Not affiliated with Salesforce. No live org is contacted.")
