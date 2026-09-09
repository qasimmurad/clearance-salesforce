"""Salesforce Lightning-flavoured styling for Clearance.

Colours are taken from the Salesforce Lightning Design System palette so the
demo reads as native to the ecosystem it is proposing a product for.
The app is deliberately pinned to a single light theme: SLDS is a light
design system, and committing to one look keeps every contrast ratio checked
rather than guessed.
"""

# --- SLDS tokens ---------------------------------------------------------
BRAND = "#0176D3"      # slds blue-50   - primary
BRAND_DARK = "#032D60"  # slds blue-20   - headers
BRAND_TINT = "#EEF4FF"  # slds blue-95   - callout backgrounds
INK = "#181818"
INK_MUTED = "#5C5C5C"
INK_SOFT = "#747474"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F3F3F3"
BORDER = "#E5E5E5"
GRID = "#EDEDED"

SUCCESS = "#2E844A"    # slds green-50
WARNING = "#FE9339"    # slds orange-50
CRITICAL = "#EA001E"   # slds red-50
SUCCESS_TINT = "#EBFCEB"
WARNING_TINT = "#FFF3E8"
CRITICAL_TINT = "#FEF1F1"

# Categorical series order, validated with the data-viz palette checker
# (lightness band, chroma floor, CVD separation, normal-vision floor all pass;
#  orange and teal warn on 3:1 surface contrast, so every chart that uses them
#  ships direct labels and a table view as the required relief).
SERIES = [BRAND, WARNING, SUCCESS, "#9050E9", "#06A59A"]

CSS = f"""
<style>
  /* ---- shell ---- */
  .stApp {{ background: {SURFACE_ALT}; }}
  .block-container {{ padding-top: 1.2rem; padding-bottom: 4rem; max-width: 1080px; }}
  header[data-testid="stHeader"] {{ background: transparent; }}
  #MainMenu, footer {{ visibility: hidden; }}
  [data-testid="stToolbar"], .stDeployButton,
  [data-testid="stDecoration"] {{ display: none !important; }}

  html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    color: {INK};
  }}

  /* ---- masthead ---- */
  .cl-masthead {{
    background: linear-gradient(96deg, {BRAND_DARK} 0%, #04396F 55%, {BRAND} 140%);
    border-radius: 10px; padding: 18px 24px; margin-bottom: 14px;
    display: flex; align-items: center; gap: 14px;
  }}
  .cl-mark {{
    width: 38px; height: 38px; border-radius: 9px; flex: 0 0 38px;
    background: {SURFACE}; color: {BRAND_DARK};
    display: flex; align-items: center; justify-content: center;
    font-weight: 750; font-size: 17px; letter-spacing: -0.5px;
  }}
  .cl-masthead h1 {{
    margin: 0; font-size: 19px; font-weight: 650; color: #fff; letter-spacing: -0.2px;
  }}
  .cl-masthead p {{ margin: 2px 0 0; font-size: 12.5px; color: #C9E2FF; }}
  .cl-org {{
    margin-left: auto; text-align: right; font-size: 11.5px;
    color: #C9E2FF; line-height: 1.5; flex: 0 0 auto;
  }}
  .cl-org b {{ color: #fff; font-weight: 600; }}

  /* ---- SLDS-style path ----
     Rendered as divs, not an <ol>: Streamlit's markdown container applies its
     own list padding and markers, which push the step numbers under the
     chevron notch. Semantics are carried by role/aria instead. */
  .cl-path {{
    display: flex !important; gap: 3px; margin: 0 0 20px;
    padding: 0 !important; list-style: none !important;
  }}
  .cl-step {{
    flex: 1; min-width: 0; padding: 8px 10px 8px 20px; font-size: 11px;
    font-weight: 600; letter-spacing: .2px; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
    background: #E9EBEE; color: {INK_SOFT};
    clip-path: polygon(0 0, calc(100% - 11px) 0, 100% 50%,
                       calc(100% - 11px) 100%, 0 100%, 11px 50%);
  }}
  .cl-step:first-child {{ padding-left: 12px;
    clip-path: polygon(0 0, calc(100% - 11px) 0, 100% 50%,
                       calc(100% - 11px) 100%, 0 100%); }}
  .cl-step.done {{ background: #C9E2FF; color: {BRAND_DARK}; }}
  .cl-step.now  {{ background: {BRAND}; color: #fff; }}

  /* ---- cards ---- */
  .cl-card {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 18px 20px; margin-bottom: 12px;
  }}
  .cl-card h3 {{ margin: 0 0 4px; font-size: 15px; font-weight: 650; }}
  .cl-card p  {{ margin: 0; font-size: 13.5px; color: {INK_MUTED}; line-height: 1.55; }}
  .cl-eyebrow {{
    font-size: 10.5px; font-weight: 700; letter-spacing: .9px;
    text-transform: uppercase; color: {INK_SOFT}; margin: 0 0 6px;
  }}

  /* ---- chips ---- */
  .cl-chip {{
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 10px; border-radius: 100px; font-size: 11.5px;
    font-weight: 600; margin: 0 6px 6px 0; border: 1px solid transparent;
  }}
  .cl-chip.brand    {{ background: {BRAND_TINT};    color: #01518F; border-color: #CCE2F7; }}
  .cl-chip.good     {{ background: {SUCCESS_TINT};  color: #1B5B32; border-color: #C4EDC7; }}
  .cl-chip.warn     {{ background: {WARNING_TINT};  color: #8C4B02; border-color: #FBD8B8; }}
  .cl-chip.critical {{ background: {CRITICAL_TINT}; color: #A00; border-color: #F7C9C9; }}
  .cl-chip.neutral  {{ background: {SURFACE_ALT};   color: {INK_MUTED}; border-color: {BORDER}; }}

  /* ---- callouts (left rule carries meaning together with the label) ---- */
  .cl-note {{
    border-left: 4px solid {BRAND}; background: {BRAND_TINT};
    padding: 13px 16px; border-radius: 0 6px 6px 0; margin: 10px 0;
    font-size: 13.5px; line-height: 1.6; color: #123;
  }}
  .cl-note.warn     {{ border-left-color: {WARNING};  background: {WARNING_TINT}; }}
  .cl-note.critical {{ border-left-color: {CRITICAL}; background: {CRITICAL_TINT}; }}
  .cl-note.good     {{ border-left-color: {SUCCESS};  background: {SUCCESS_TINT}; }}
  .cl-note b.cl-note-t {{ display: block; margin-bottom: 3px; font-size: 12px;
                text-transform: uppercase; letter-spacing: .5px; }}
  .cl-note .lead {{ display: block; font-size: 14px; font-weight: 650;
                    margin-bottom: 5px; color: {INK}; }}

  /* ---- stat tiles ---- */
  .cl-tile {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 14px 16px; height: 100%;
  }}
  .cl-tile .lab {{ font-size: 11.5px; color: {INK_SOFT}; line-height: 1.4;
                   min-height: 32px; display: block; }}
  .cl-tile .val {{ font-size: 27px; font-weight: 680; letter-spacing: -.8px;
                   line-height: 1.15; margin-top: 5px; }}
  .cl-tile .was {{ font-size: 11.5px; color: {INK_SOFT}; margin-top: 3px; }}

  .cl-hero {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-left: 4px solid {BRAND};
    border-radius: 8px; padding: 20px 24px; margin-bottom: 12px;
  }}
  .cl-hero .fig {{ font-size: 52px; font-weight: 700; letter-spacing: -2px;
                   line-height: 1; color: {BRAND_DARK}; }}
  .cl-hero .cap {{ font-size: 13.5px; color: {INK_MUTED}; margin-top: 6px; }}

  /* ---- data rows ---- */
  .cl-row {{
    display: flex; justify-content: space-between; gap: 16px;
    padding: 9px 0; border-bottom: 1px solid {GRID}; font-size: 13.5px;
  }}
  .cl-row:last-child {{ border-bottom: none; }}
  .cl-row .k {{ color: {INK_MUTED}; }}
  .cl-row .v {{ font-weight: 600; text-align: right; }}

  /* ---- code ---- */
  .stCodeBlock, .stCodeBlock pre {{ font-size: 12.2px !important; }}

  /* ---- buttons ---- */
  .stButton > button {{
    border-radius: 6px; font-weight: 600; font-size: 13.5px;
    padding: .5rem 1.1rem; border: 1px solid #C9C9C9;
  }}
  .stButton > button[kind="primary"] {{ border-color: {BRAND}; }}
  .stButton > button:focus-visible {{
    outline: 3px solid #1B96FF !important; outline-offset: 2px !important;
  }}

  /* visible focus everywhere - part of the accessibility claim this app makes */
  a:focus-visible, [role="button"]:focus-visible, summary:focus-visible {{
    outline: 3px solid #1B96FF; outline-offset: 2px;
  }}
  .cl-sr {{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); }}
</style>
"""


def chip(label: str, tone: str = "neutral", icon: str = "") -> str:
    """A status pill. Always carries a text label, never colour alone."""
    lead = f"{icon} " if icon else ""
    return f'<span class="cl-chip {tone}">{lead}{label}</span>'


def note(body: str, title: str = "", tone: str = "brand") -> str:
    head = f'<b class="cl-note-t">{title}</b>' if title else ""
    return f'<div class="cl-note {tone}">{head}{body}</div>'


def tile(label: str, value: str, was: str = "") -> str:
    sub = f'<div class="was">{was}</div>' if was else ""
    return (f'<div class="cl-tile"><span class="lab">{label}</span>'
            f'<div class="val">{value}</div>{sub}</div>')


def row(k: str, v: str) -> str:
    return f'<div class="cl-row"><span class="k">{k}</span><span class="v">{v}</span></div>'
