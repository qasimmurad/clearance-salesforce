"""Charts for the impact view.

Colour choices here were run through the data-viz palette validator rather
than eyeballed. Two results worth recording:

  * blue + violet (#0176D3 / #9050E9) FAILED CVD separation at Delta-E 3.3 for
    deuteranopes. Two lines a large minority of readers cannot tell apart is
    not acceptable in an app whose pitch is accessibility, so it was dropped.

  * blue + grey (#0176D3 / #767676) is the emphasis pattern: one series carries
    the story, the baseline recedes. It fails the categorical chroma floor by
    design - "reads grey" is the intent, not a defect - and clears CVD
    separation at Delta-E 15.2 and 3:1 surface contrast.

Every chart also ships a table view, which is both the accessibility fallback
and the relief the validator requires for any sub-3:1 fill.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

import catalog
from theme import BRAND, GRID, INK, INK_MUTED, INK_SOFT, SURFACE

BASELINE = "#767676"

_AXIS = dict(
    grid=True, gridColor=GRID, gridWidth=1, gridDash=[],   # hairline, solid, never dashed
    domain=False, ticks=False,
    labelColor=INK_SOFT, labelFontSize=11, labelPadding=6,
    titleColor=INK_SOFT, titleFontSize=11, titleFontWeight=500, titlePadding=12,
)

S_CURRENT = "Current pace"
S_CLEARANCE = "With Clearance"


def backlog_frame() -> pd.DataFrame:
    rows = []
    for w, a, b in zip(catalog.BACKLOG_WEEKS, catalog.BACKLOG_BASE, catalog.BACKLOG_CLEARANCE):
        rows.append({"week": w, "series": S_CURRENT, "open": a})
        rows.append({"week": w, "series": S_CLEARANCE, "open": b})
    return pd.DataFrame(rows)


def backlog_chart() -> alt.LayerChart:
    df = backlog_frame()
    last = df[df.week == df.week.max()]

    scale = alt.Scale(domain=[S_CURRENT, S_CLEARANCE], range=[BASELINE, BRAND])
    colour = alt.Color(
        "series:N", scale=scale,
        legend=alt.Legend(title=None, orient="top", direction="horizontal",
                          symbolType="stroke", symbolStrokeWidth=3, symbolSize=160,
                          labelColor=INK_MUTED, labelFontSize=11.5, offset=4),
    )

    base = alt.Chart(df).encode(
        x=alt.X("week:Q",
                scale=alt.Scale(domain=[0, 13.6], nice=False),
                axis=alt.Axis(title="Weeks from launch", values=[0, 2, 4, 6, 8, 10],
                              format="d", labelOverlap=False, **_AXIS)),
        y=alt.Y("open:Q",
                scale=alt.Scale(domain=[0, 120], nice=False),
                axis=alt.Axis(title="Open requests", values=[0, 30, 60, 90, 120],
                              format="d", labelOverlap=False, **_AXIS)),
    )

    line = base.mark_line(strokeWidth=2, strokeCap="round", strokeJoin="round").encode(
        color=colour,
        tooltip=[alt.Tooltip("series:N", title="Scenario"),
                 alt.Tooltip("week:Q", title="Week"),
                 alt.Tooltip("open:Q", title="Open requests")],
    )

    # End markers carry a 2px surface ring so they stay legible where they cross.
    dot = alt.Chart(last).mark_point(
        filled=True, size=90, stroke=SURFACE, strokeWidth=2,
    ).encode(x="week:Q", y="open:Q", color=alt.Color("series:N", scale=scale, legend=None))

    # Direct labels wear ink, never the series colour - the dot beside them
    # carries the identity.
    label = alt.Chart(last).mark_text(
        align="left", dx=11, fontSize=12.5, fontWeight=600, color=INK,
    ).encode(x="week:Q", y="open:Q", text=alt.Text("open:Q", format="d"))

    return (line + dot + label).properties(height=250).configure_view(stroke=None)


def triage_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [{"bucket": b, "count": n, "what": w} for b, n, w in catalog.TRIAGE]
    )


def triage_chart() -> alt.LayerChart:
    df = triage_frame()
    order = df.sort_values("count", ascending=False)["bucket"].tolist()

    base = alt.Chart(df).encode(
        y=alt.Y("bucket:N", sort=order, title=None,
                axis=alt.Axis(labelColor=INK, labelFontSize=12, labelLimit=260,
                              domain=False, ticks=False, grid=False, labelPadding=8)),
        x=alt.X("count:Q", title=None, scale=alt.Scale(domain=[0, 33], nice=False),
                axis=None),   # every bar is directly labelled, so the axis is redundant
    )

    # One series, one colour. A value ramp here would double-encode bar length.
    bar = base.mark_bar(size=18, cornerRadiusEnd=4, color=BRAND).encode(
        tooltip=[alt.Tooltip("bucket:N", title="Bucket"),
                 alt.Tooltip("count:Q", title="Requests"),
                 alt.Tooltip("what:N", title="What happens")],
    )
    label = base.mark_text(align="left", dx=8, fontSize=12.5,
                           fontWeight=600, color=INK).encode(text=alt.Text("count:Q"))

    return (bar + label).properties(height=190).configure_view(stroke=None)


def backlog_table() -> pd.DataFrame:
    return pd.DataFrame({
        "Week": catalog.BACKLOG_WEEKS,
        S_CURRENT: catalog.BACKLOG_BASE,
        S_CLEARANCE: catalog.BACKLOG_CLEARANCE,
    }).set_index("Week")


def triage_table() -> pd.DataFrame:
    return (triage_frame()
            .rename(columns={"bucket": "Bucket", "count": "Requests", "what": "What happens"})
            .set_index("Bucket"))
