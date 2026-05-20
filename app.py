import streamlit as st
import anthropic
import json
import re
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CommodityPulse – Procurement Intelligence",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_QUERIES = 2
TODAY      = datetime.today()
TODAY_STR  = TODAY.strftime("%d %B %Y")

DEFAULT_MATERIALS = sorted([
    "Aluminium Cans", "Aluminium Foil", "Aluminium Sheet", "Caustic Soda",
    "Cement", "Chlorine", "Cocoa Butter", "Copper Wire", "Corrugated Board",
    "Cotton Yarn", "Diesel Fuel", "Electricity (Industrial)", "Ethanol",
    "Flat Glass", "Flexible Packaging Film", "Float Glass", "Glass Bottles",
    "HDPE Resin", "Kraft Paper", "Labels & Sleeves", "LDPE Film",
    "Logistics – Air Freight", "Logistics – Road Freight", "Logistics – Sea Freight",
    "Natural Gas (Industrial)", "Newsprint", "Nitrogen Gas", "Palm Oil",
    "PET Bottles", "PET Resin", "Polypropylene Resin", "Shrink Wrap Film",
    "Silica Sand", "Soda Ash", "Soybean Oil", "Stainless Steel Coil",
    "Steel Coils (HRC)", "Sugar (Refined)", "Sulphuric Acid",
    "Timber (Softwood)", "Tissue Paper", "Wheat Flour", "White Sugar",
    "Wood Pulp", "Zinc (LME)",
])

RISK_CFG = {
    15: ("LOW",      "#22c55e", "#052e16", "#16a34a"),
    45: ("MODERATE", "#facc15", "#1c1a00", "#ca8a04"),
    70: ("HIGH",     "#f97316", "#1c0a00", "#ea580c"),
    98: ("CRITICAL", "#ef4444", "#1c0000", "#dc2626"),
}
VALID_SCORES = [15, 45, 70, 98]

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; background:#080d16; color:#e5e7eb; }
.stApp { background:#080d16; }
.block-container { max-width:1100px; padding-top:1.5rem; padding-bottom:4rem; }
h1,h2,h3 { font-family:'DM Sans',sans-serif; color:#f9fafb; }
#MainMenu,footer,header { visibility:hidden; }

.topbar {
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 20px; background:linear-gradient(90deg,#0f172a,#0a1628);
  border-bottom:1px solid #1e3a5f; border-radius:10px; margin-bottom:1.5rem;
}
.brand-name { font-weight:700; font-size:1rem; color:#f9fafb; }
.brand-sub  { font-size:0.62rem; color:#4b5563; letter-spacing:0.1em; }
.date-pill  {
  font-size:0.68rem; color:#4b5563; letter-spacing:0.08em;
  background:rgba(59,130,246,0.08); border:1px solid #1e3a5f;
  border-radius:6px; padding:4px 10px; font-family:'DM Mono',monospace;
}

.card {
  background:linear-gradient(135deg,#0f172a,#111827);
  border:1px solid #1e3a5f; border-radius:14px;
  padding:22px; margin-bottom:16px;
  box-shadow:0 4px 24px rgba(0,0,0,0.4);
}
.card-warn  { border-color:rgba(250,204,21,0.3); background:rgba(250,204,21,0.04); }
.card-green { border-color:rgba(34,197,94,0.3);  background:rgba(34,197,94,0.04);  }

.slabel {
  font-size:0.62rem; font-weight:700; color:#6b7280;
  letter-spacing:0.12em; text-transform:uppercase;
  margin-bottom:10px; font-family:'DM Mono',monospace;
}

.risk-badge {
  display:inline-block; border-radius:6px;
  padding:5px 14px; font-weight:700; font-size:0.78rem;
  letter-spacing:0.06em; font-family:'DM Mono',monospace;
}

.module-header {
  font-size:0.72rem; font-weight:700; color:#3b82f6;
  letter-spacing:0.15em; text-transform:uppercase;
  margin-bottom:4px; font-family:'DM Mono',monospace;
}
.module-title {
  font-size:1.15rem; font-weight:700; color:#f9fafb;
  margin-bottom:16px; letter-spacing:-0.01em;
}

.ft-table { width:100%; border-collapse:collapse; font-size:0.82rem; }
.ft-table th {
  background:#0f172a; color:#6b7280; font-size:0.62rem;
  letter-spacing:0.1em; text-transform:uppercase; padding:8px 12px;
  border-bottom:1px solid #1e3a5f; font-family:'DM Mono',monospace;
  text-align:left; font-weight:600;
}
.ft-table td { padding:9px 12px; border-bottom:1px solid #0f172a; color:#d1d5db; vertical-align:top; }
.ft-table tr:last-child td { border-bottom:none; }
.ft-key { color:#93c5fd; font-family:'DM Mono',monospace; font-size:0.78rem; white-space:nowrap; }
.ft-val { color:#e5e7eb; }

.ch-table { width:100%; border-collapse:collapse; font-size:0.8rem; margin-top:8px; }
.ch-table th {
  background:#0a1121; color:#6b7280; font-size:0.6rem;
  letter-spacing:0.1em; text-transform:uppercase; padding:9px 12px;
  border-bottom:2px solid #1e3a5f; font-family:'DM Mono',monospace; text-align:left;
}
.ch-table td { padding:9px 12px; border-bottom:1px solid #0f172a; color:#d1d5db; vertical-align:top; line-height:1.55; }
.ch-table tr:hover td { background:rgba(59,130,246,0.04); }
.ch-table tr:last-child td { border-bottom:none; }
.weight-pill {
  display:inline-block; background:rgba(59,130,246,0.15);
  border:1px solid rgba(59,130,246,0.4); border-radius:20px;
  padding:2px 9px; font-weight:700; color:#93c5fd;
  font-family:'DM Mono',monospace; font-size:0.78rem;
}
.proxy-tag {
  display:inline-block; background:rgba(250,204,21,0.1);
  border:1px solid rgba(250,204,21,0.3); border-radius:4px;
  padding:1px 6px; font-size:0.68rem; color:#fde68a;
  font-family:'DM Mono',monospace; margin-left:4px;
}

.inf-table { width:100%; border-collapse:collapse; font-size:0.8rem; margin-top:8px; }
.inf-table th {
  background:#0a1121; color:#6b7280; font-size:0.6rem;
  letter-spacing:0.1em; text-transform:uppercase; padding:8px 12px;
  border-bottom:2px solid #1e3a5f; font-family:'DM Mono',monospace; text-align:left;
}
.inf-table td { padding:9px 12px; border-bottom:1px solid #0f172a; color:#d1d5db; vertical-align:top; }
.inf-table tr:last-child td { border-bottom:none; }
.inf-pos { color:#f97316; font-weight:700; font-family:'DM Mono',monospace; }
.inf-neg { color:#22c55e; font-weight:700; font-family:'DM Mono',monospace; }
.inf-neu { color:#facc15; font-weight:700; font-family:'DM Mono',monospace; }
.inf-total {
  background:rgba(59,130,246,0.08) !important;
  font-weight:700; font-family:'DM Mono',monospace;
  border-top:1px solid #1e3a5f !important;
}

.bullet-block {
  border-left:2px solid #1e3a5f; padding:10px 14px;
  margin-bottom:10px; border-radius:0 6px 6px 0;
  background:rgba(255,255,255,0.02);
}
.bullet-title { color:#93c5fd; font-weight:600; font-size:0.84rem; }
.bullet-body  { color:#d1d5db; font-size:0.82rem; line-height:1.65; margin-top:4px; }

.scenario-best  { border-left:3px solid #22c55e; padding:10px 14px; background:rgba(34,197,94,0.04);  border-radius:0 8px 8px 0; margin-bottom:8px; }
.scenario-base  { border-left:3px solid #facc15; padding:10px 14px; background:rgba(250,204,21,0.04); border-radius:0 8px 8px 0; margin-bottom:8px; }
.scenario-worst { border-left:3px solid #ef4444; padding:10px 14px; background:rgba(239,68,68,0.04);  border-radius:0 8px 8px 0; margin-bottom:8px; }
.sc-label { font-size:0.62rem; font-weight:700; letter-spacing:0.1em; margin-bottom:4px; font-family:'DM Mono',monospace; }
.sc-text  { font-size:0.82rem; color:#d1d5db; line-height:1.6; }

.ref-link { font-size:0.7rem; color:#3b82f6; word-break:break-all; line-height:1.8; font-family:'DM Mono',monospace; }
.scope-note {
  background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.2);
  border-radius:8px; padding:12px 16px;
  font-size:0.8rem; color:#93c5fd; line-height:1.6; margin-bottom:16px;
}
.confidence-med  { color:#facc15; font-weight:700; }
.confidence-high { color:#22c55e; font-weight:700; }
.confidence-low  { color:#f97316; font-weight:700; }

.query-counter {
  background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25);
  border-radius:8px; padding:10px 16px; font-size:0.8rem; color:#fca5a5;
  margin-bottom:16px; font-family:'DM Mono',monospace;
}
.divider { border:none; border-top:1px solid #1e3a5f; margin:20px 0; }

div[data-testid="stButton"] button {
  background:linear-gradient(135deg,#1d4ed8,#2563eb);
  color:#fff; font-weight:700; border:none; border-radius:10px;
  padding:0.55rem 2rem; font-family:'DM Sans',sans-serif;
  font-size:0.9rem; letter-spacing:0.04em;
}
div[data-testid="stButton"] button:hover {
  background:linear-gradient(135deg,#2563eb,#3b82f6);
  box-shadow:0 0 20px rgba(59,130,246,0.3);
}
div[data-testid="stButton"] button:disabled { background:#1e3a5f; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_api_key():
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        st.error("API key not configured. Add ANTHROPIC_API_KEY to Streamlit Secrets (Settings → Secrets).")
        st.stop()


def load_materials():
    try:
        df = pd.read_excel("materials.xlsx")
        for col in ["Material", "material", "L3 Category", "Category", "Service", "Name"]:
            if col in df.columns:
                items = df[col].dropna().astype(str).str.strip()
                items = [i for i in items if i]
                if items:
                    return sorted(items)
        first_col = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
        return sorted([i for i in first_col if i]) or DEFAULT_MATERIALS
    except Exception:
        return DEFAULT_MATERIALS


def snap_risk(score):
    try:
        score = int(score)
    except Exception:
        return 45
    return min(VALID_SCORES, key=lambda x: abs(x - score))


def risk_badge(score):
    score = snap_risk(score)
    label, color, bg, border = RISK_CFG[score]
    return (
        f'<span class="risk-badge" style="color:{color};background:{bg};border:1.5px solid {border};">'
        f'● {score} — {label}</span>'
    )


def extract_text(response):
    parts = []
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            parts.append(block.text)
    return "\n".join(parts)


def parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text.strip())
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        return json.loads(m.group())
    return json.loads(text)


def month_labels(n):
    labels = []
    d = TODAY
    for i in range(n):
        d = d.replace(day=1)
        if i == 0:
            d = d.replace(month=d.month % 12 + 1)
            if d.month == 1:
                d = d.replace(year=d.year + 1)
        labels.append(d.strftime("%B %Y"))
    return labels


def confidence_class(level):
    l = str(level).lower()
    if "high" in l:   return "confidence-high"
    if "medium" in l or "med" in l: return "confidence-med"
    return "confidence-low"


# ── API calls ──────────────────────────────────────────────────────────────────

def call_module1(material, region, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""You are a senior procurement cost-modelling analyst. Today is {TODAY_STR}.

The user has asked for a Cost Head Analysis for: "{material}" in the region: {region}.

Use your knowledge and web search to find the most current benchmark data and pricing indices available for this material and region.

Return ONLY a valid JSON object, no markdown, no explanation:
{{
  "scope_note": "One sentence: note if this is within direct calibrated scope or a closest-fit benchmark map. Mention if proxies are used.",
  "freshness": {{
    "check_date": "{TODAY_STR}",
    "region": "{region}",
    "tax_basis": "e.g. N/A or Ex-works or DAP",
    "primary_benchmarks": "Comma-separated list of the main indices or price series used, with issuing body",
    "most_recent_source_date": "Date of the most recent data point found (DD Mon YYYY)",
    "confidence_level": "High, Medium, or Low",
    "narrative": "2-3 sentences explaining the data quality, what direct pricing is available, and where proxies are used."
  }},
  "cost_heads": [
    {{
      "name": "Cost head name (e.g. Energy)",
      "weight_pct": 30,
      "why_included": "One clear sentence on why this cost head matters for this material.",
      "best_fit_index": "Name of the index or proxy used",
      "why_index": "One clear sentence on why this index is the best public fit.",
      "is_proxy": true
    }}
  ]
}}

Rules:
- Provide 4 to 6 cost heads that together sum to 100%.
- weight_pct values must sum to exactly 100.
- is_proxy is true if no direct price series exists and a proxy is used; false if a direct benchmark is available.
- Focus entirely on {region} supply and pricing context.
- Be specific and factual. Qualify any estimate clearly.
- The JSON must be valid and parseable."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    return parse_json(extract_text(response))


def call_module2(material, region, periods, cost_heads, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    ch_summary = json.dumps([
        {"name": c["name"], "weight_pct": c["weight_pct"], "index": c["best_fit_index"]}
        for c in cost_heads
    ], indent=2)
    labels = month_labels(periods)
    prompt = f"""You are a senior procurement cost analyst. Today is {TODAY_STR}.

The user wants an Inflation Impact projection for: "{material}" in {region}.

The cost head structure already identified is:
{ch_summary}

Use web search to find the latest available forward price signals, futures curves, and analyst forecasts for each cost head's benchmark index. Then project the cost impact for each of the next {periods} months:
Months to project: {labels}

Return ONLY a valid JSON object:
{{
  "analysis_basis": "One sentence describing the main data sources used for the projections.",
  "months": [
    {{
      "label": "Month Year",
      "cost_head_impacts": [
        {{
          "name": "Cost head name",
          "weight_pct": 30,
          "projected_change_pct": 2.5,
          "direction": "up or down or stable",
          "driver": "One short sentence on the main price driver for this period."
        }}
      ],
      "weighted_total_pct": 1.1,
      "key_driver": "One sentence on the dominant factor driving the total impact this month."
    }}
  ],
  "key_assumptions": "2-3 sentences listing the main assumptions underpinning the projections.",
  "disclaimer": "This projection is an estimate based on publicly available forward price signals as of {TODAY_STR}. It is not a financial model and should not be used as the sole basis for pricing decisions."
}}

Rules:
- projected_change_pct is the estimated percentage change in that cost head's input cost for that month vs current levels. Positive = cost increase. Negative = cost decrease.
- weighted_total_pct = sum of (projected_change_pct * weight_pct / 100) across all cost heads for that month.
- Be specific. Use actual futures levels, analyst consensus ranges, or clearly labelled estimates.
- Focus entirely on {region} context.
- The JSON must be valid and parseable."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    return parse_json(extract_text(response))


def call_module3(material, region, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""You are a senior procurement supply risk analyst. Today is {TODAY_STR}.

The user wants a Shortage Tracker analysis for: "{material}" in {region}.

Use web search extensively to find the most current available data: production issues, trade flows, import dependence, logistics constraints, geopolitical exposure, sanctions, energy input risks, weather impacts, policy changes, and relevant market developments.

Return ONLY a valid JSON object, no markdown:
{{
  "current_supply_risk": 45,
  "forecasted_supply_risk": 70,
  "variables": [
    {{
      "title": "Short descriptive title for this variable (e.g. 'Energy input cost pressure persists')",
      "body": "3-5 sentences of detailed factual analysis. Include specific figures, dates, and sources where available. Use the same depth and style as a professional procurement intelligence briefing."
    }}
  ],
  "forecast_6m": "One detailed paragraph (3-4 sentences) on the 6-month availability outlook from {TODAY_STR}. Be specific about the key events and timing.",
  "forecast_12m_best": "One specific sentence describing the best-case 12-month scenario with the conditions required.",
  "forecast_12m_base": "One specific sentence describing the base-case 12-month scenario.",
  "forecast_12m_worst": "One specific sentence describing the worst-case 12-month scenario.",
  "additional_comments": [
    {{
      "title": "Short title for the watchpoint",
      "body": "2-4 sentences of insight not repeated from variables above. Focus on L3 downstream impacts, buyer watchpoints, concentration risks, or upcoming review triggers.",
      "references": ["url1", "url2"]
    }}
  ],
  "all_references": ["url1", "url2", "url3"]
}}

Rules:
- current_supply_risk and forecasted_supply_risk must be ONLY one of: 15, 45, 70, 98.
- 15=least risk, 98=highest risk.
- Provide 4 to 6 variable bullets and 3 to 4 additional comment bullets.
- References must be real URLs from official bodies, industry associations, exchanges, or credible trade publications.
- Focus entirely on {region} supply context.
- Do not invent data. Where uncertain, qualify with 'reported' or 'estimated'.
- The JSON must be valid and parseable."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    return parse_json(extract_text(response))


# ── Display functions ──────────────────────────────────────────────────────────

def display_module1(d, material, region):
    f = d.get("freshness", {})
    scope = d.get("scope_note", "")
    cost_heads = d.get("cost_heads", [])

    st.markdown('<div class="module-header">MODULE 1</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-title">Cost Head Analysis</div>', unsafe_allow_html=True)

    if scope:
        st.markdown(f'<div class="scope-note">{material} ({region}) — {scope}</div>', unsafe_allow_html=True)

    # Freshness block
    st.markdown('<div class="slabel">B. Freshness Block</div>', unsafe_allow_html=True)
    conf_cls = confidence_class(f.get("confidence_level", ""))
    rows = [
        ("Market status check date", f.get("check_date", TODAY_STR)),
        ("Region", f.get("region", region)),
        ("Tax basis", f.get("tax_basis", "N/A")),
        ("Primary benchmark(s) used", f.get("primary_benchmarks", "—")),
        ("Most recent source date found", f.get("most_recent_source_date", "—")),
        ("Confidence level",
         f'<span class="{conf_cls}">{f.get("confidence_level","—")}</span>'),
    ]
    rows_html = "".join(
        f'<tr><td class="ft-key">{k}</td><td class="ft-val">{v}</td></tr>'
        for k, v in rows
    )
    st.markdown(
        f'<div class="card"><table class="ft-table"><thead><tr>'
        f'<th>Item</th><th>Value</th></tr></thead><tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True,
    )
    if f.get("narrative"):
        st.markdown(
            f'<div class="card" style="padding:14px 20px;">'
            f'<div style="font-size:0.82rem;color:#d1d5db;line-height:1.7;">{f["narrative"]}</div></div>',
            unsafe_allow_html=True,
        )

    # Cost-head table
    st.markdown('<div class="slabel" style="margin-top:16px;">C. Cost-Head Table</div>', unsafe_allow_html=True)
    ch_rows = ""
    for ch in cost_heads:
        proxy_tag = '<span class="proxy-tag">PROXY</span>' if ch.get("is_proxy") else ""
        ch_rows += (
            f'<tr>'
            f'<td><strong style="color:#f9fafb;">{ch.get("name","")}</strong></td>'
            f'<td><span class="weight-pill">{ch.get("weight_pct",0)}%</span></td>'
            f'<td>{ch.get("why_included","")}</td>'
            f'<td>{ch.get("best_fit_index","")}{proxy_tag}</td>'
            f'<td>{ch.get("why_index","")}</td>'
            f'</tr>'
        )
    st.markdown(
        f'<div class="card"><table class="ch-table">'
        f'<thead><tr><th>Cost Head</th><th>Weight %</th><th>Why Included</th>'
        f'<th>Best-Fit Index / Proxy</th><th>Why This Index / Proxy</th></tr></thead>'
        f'<tbody>{ch_rows}</tbody></table></div>',
        unsafe_allow_html=True,
    )
    return cost_heads


def display_module2(d, material, region, periods):
    months_data = d.get("months", [])

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="module-header">MODULE 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-title">Inflation Impact Projection</div>', unsafe_allow_html=True)

    if d.get("analysis_basis"):
        st.markdown(
            f'<div class="scope-note">{d["analysis_basis"]}</div>',
            unsafe_allow_html=True,
        )

    # Build header from cost head names
    if months_data:
        heads = [h["name"] for h in months_data[0].get("cost_head_impacts", [])]
        th_heads = "".join(f"<th>{h}</th>" for h in heads)
        header = f"<tr><th>Month</th>{th_heads}<th>Weighted Total Impact</th><th>Key Driver</th></tr>"

        rows_html = ""
        for m in months_data:
            cells = ""
            for imp in m.get("cost_head_impacts", []):
                pct = imp.get("projected_change_pct", 0)
                try:
                    pct_f = float(pct)
                except Exception:
                    pct_f = 0
                cls = "inf-pos" if pct_f > 0 else ("inf-neg" if pct_f < 0 else "inf-neu")
                sign = "+" if pct_f > 0 else ""
                cells += f'<td class="{cls}">{sign}{pct_f:.1f}%<br><span style="font-size:0.68rem;color:#6b7280;font-weight:400;">{imp.get("driver","")}</span></td>'

            total = m.get("weighted_total_pct", 0)
            try:
                total_f = float(total)
            except Exception:
                total_f = 0
            t_cls = "inf-pos" if total_f > 0 else ("inf-neg" if total_f < 0 else "inf-neu")
            sign = "+" if total_f > 0 else ""
            rows_html += (
                f'<tr>'
                f'<td style="color:#f9fafb;font-weight:600;white-space:nowrap;">{m.get("label","")}</td>'
                f'{cells}'
                f'<td class="inf-total {t_cls}">{sign}{total_f:.2f}%</td>'
                f'<td style="font-size:0.78rem;color:#d1d5db;">{m.get("key_driver","")}</td>'
                f'</tr>'
            )

        st.markdown(
            f'<div class="card" style="overflow-x:auto;">'
            f'<table class="inf-table"><thead>{header}</thead><tbody>{rows_html}</tbody></table></div>',
            unsafe_allow_html=True,
        )

    if d.get("key_assumptions"):
        st.markdown(
            f'<div class="card card-warn"><div class="slabel">Key Assumptions</div>'
            f'<div style="font-size:0.82rem;color:#d1d5db;line-height:1.7;">{d["key_assumptions"]}</div></div>',
            unsafe_allow_html=True,
        )
    if d.get("disclaimer"):
        st.markdown(
            f'<div style="font-size:0.72rem;color:#4b5563;margin-top:8px;">⚠ {d["disclaimer"]}</div>',
            unsafe_allow_html=True,
        )


def display_module3(d, material, region):
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="module-header">MODULE 3</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-title">Shortage Tracker</div>', unsafe_allow_html=True)

    # Risk scores
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<div class="card"><div class="slabel">Current Supply Risk</div>'
            f'{risk_badge(d.get("current_supply_risk", 45))}</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="card"><div class="slabel">Forecasted Supply Risk</div>'
            f'{risk_badge(d.get("forecasted_supply_risk", 45))}</div>',
            unsafe_allow_html=True,
        )

    # Variables
    variables = d.get("variables", [])
    if variables:
        st.markdown('<div class="slabel" style="margin-top:8px;">Variables Impacting Availability</div>', unsafe_allow_html=True)
        html = '<div class="card">'
        for v in variables:
            title = v.get("title", "")
            body  = v.get("body", "")
            html += (
                f'<div class="bullet-block">'
                f'<div class="bullet-title">&gt; {title}</div>'
                f'<div class="bullet-body">{body}</div>'
                f'</div>'
            )
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    # Availability forecast
    st.markdown('<div class="slabel" style="margin-top:4px;">Availability Forecast</div>', unsafe_allow_html=True)
    f6  = d.get("forecast_6m", "")
    fb  = d.get("forecast_12m_best", "")
    fba = d.get("forecast_12m_base", "")
    fw  = d.get("forecast_12m_worst", "")
    st.markdown(
        f'<div class="card">'
        f'<div class="slabel" style="color:#4b5563;">6-Month Outlook</div>'
        f'<div style="font-size:0.82rem;color:#d1d5db;line-height:1.7;margin-bottom:16px;">'
        f'&gt; Next 6 months: {f6}</div>'
        f'<div class="slabel" style="color:#4b5563;">12-Month Scenarios</div>'
        f'<div class="scenario-best"><div class="sc-label" style="color:#22c55e;">▲ BEST CASE</div>'
        f'<div class="sc-text">{fb}</div></div>'
        f'<div class="scenario-base"><div class="sc-label" style="color:#facc15;">◆ BASE CASE</div>'
        f'<div class="sc-text">{fba}</div></div>'
        f'<div class="scenario-worst"><div class="sc-label" style="color:#ef4444;">▼ WORST CASE</div>'
        f'<div class="sc-text">{fw}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Additional comments
    comments = d.get("additional_comments", [])
    if comments:
        st.markdown('<div class="slabel" style="margin-top:4px;">Additional Comments</div>', unsafe_allow_html=True)
        html = '<div class="card">'
        for c in comments:
            title = c.get("title", "")
            body  = c.get("body", "")
            refs  = c.get("references", [])
            ref_html = "".join(
                f'<a href="{r}" target="_blank" class="ref-link">• {r}</a><br>'
                for r in refs
            )
            html += (
                f'<div class="bullet-block">'
                f'<div class="bullet-title">&gt; {title}</div>'
                f'<div class="bullet-body">{body}</div>'
            )
            if ref_html:
                html += f'<div style="margin-top:6px;">{ref_html}</div>'
            html += '</div>'
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    # All references
    all_refs = d.get("all_references", [])
    if all_refs:
        with st.expander("📎 All References"):
            for r in all_refs:
                st.markdown(
                    f'<a href="{r}" target="_blank" class="ref-link">{r}</a>',
                    unsafe_allow_html=True,
                )


# ── Session state init ─────────────────────────────────────────────────────────
if "query_count" not in st.session_state:
    st.session_state["query_count"] = 0
if "result_m1"  not in st.session_state:
    st.session_state["result_m1"] = None
if "result_m2"  not in st.session_state:
    st.session_state["result_m2"] = None
if "result_m3"  not in st.session_state:
    st.session_state["result_m3"] = None
if "last_params" not in st.session_state:
    st.session_state["last_params"] = {}

# ── Load materials ─────────────────────────────────────────────────────────────
materials_list = load_materials()

# ── Top bar ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="topbar">'
    f'<div><div class="brand-name">⬡ CommodityPulse</div>'
    f'<div class="brand-sub">PROCUREMENT INTELLIGENCE PLATFORM</div></div>'
    f'<div class="date-pill">ANALYSIS DATE: {TODAY_STR.upper()}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── Sidebar: inputs ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Analysis Parameters")
    st.markdown("---")

    selected_material = st.selectbox(
        "Select L3 Category / Material",
        options=materials_list,
        help="Select the material or service to analyse.",
    )

    selected_region = st.selectbox(
        "Region",
        options=["Europe", "North America", "Asia Pacific", "Middle East & Africa", "Latin America"],
        index=0,
    )

    st.markdown("---")
    st.markdown("**Select Analysis Modules**")

    run_m2 = st.checkbox("Module 2 — Inflation Impact", value=False)
    run_m3 = st.checkbox("Module 3 — Shortage Tracker", value=False)

    forecast_periods = 3
    if run_m2:
        forecast_periods = st.select_slider(
            "Forecast period (months)",
            options=[1, 2, 3, 4, 5, 6],
            value=3,
        )

    st.markdown("---")

    queries_left = MAX_QUERIES - st.session_state["query_count"]
    if queries_left > 0:
        st.markdown(
            f'<div style="font-size:0.72rem;color:#6b7280;font-family:\'DM Mono\',monospace;">'
            f'Trial queries remaining: <strong style="color:#f9fafb;">{queries_left} / {MAX_QUERIES}</strong></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-size:0.72rem;color:#ef4444;font-family:\'DM Mono\',monospace;">'
            'Trial limit reached (2/2). Contact us to unlock full access.</div>',
            unsafe_allow_html=True,
        )

    analyse_btn = st.button(
        "Run Analysis →",
        use_container_width=True,
        disabled=(queries_left <= 0),
    )

    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.68rem;color:#374151;line-height:1.8;">'
        'Module 1 (Cost Heads) always runs.<br>'
        'Module 2 requires Module 1 output.<br>'
        'Module 3 fetches live supply data.<br><br>'
        '⚠ All outputs are AI-generated estimates. Validate before decisions.'
        '</div>',
        unsafe_allow_html=True,
    )

# ── Main panel: run analysis ───────────────────────────────────────────────────
if analyse_btn:
    api_key = get_api_key()
    st.session_state["query_count"] += 1
    st.session_state["result_m1"] = None
    st.session_state["result_m2"] = None
    st.session_state["result_m3"] = None
    st.session_state["last_params"] = {
        "material": selected_material,
        "region": selected_region,
        "run_m2": run_m2,
        "run_m3": run_m3,
        "periods": forecast_periods,
    }

    with st.spinner(f"Running Module 1 — Cost Head Analysis for {selected_material} ({selected_region})..."):
        try:
            st.session_state["result_m1"] = call_module1(selected_material, selected_region, api_key)
        except Exception as e:
            st.error(f"Module 1 error: {e}")

    if run_m2 and st.session_state["result_m1"]:
        cost_heads = st.session_state["result_m1"].get("cost_heads", [])
        with st.spinner(f"Running Module 2 — Inflation Impact ({forecast_periods}-month projection)..."):
            try:
                st.session_state["result_m2"] = call_module2(
                    selected_material, selected_region, forecast_periods, cost_heads, api_key
                )
            except Exception as e:
                st.error(f"Module 2 error: {e}")

    if run_m3:
        with st.spinner(f"Running Module 3 — Shortage Tracker (fetching live data)..."):
            try:
                st.session_state["result_m3"] = call_module3(selected_material, selected_region, api_key)
            except Exception as e:
                st.error(f"Module 3 error: {e}")

# ── Display results ────────────────────────────────────────────────────────────
p = st.session_state.get("last_params", {})
mat = p.get("material", "")
reg = p.get("region", "Europe")

if st.session_state["result_m1"]:
    st.markdown(
        f'<div style="font-size:0.68rem;color:#6b7280;margin-bottom:4px;font-family:\'DM Mono\',monospace;">'
        f'RESULTS FOR</div>'
        f'<h2 style="margin:0 0 20px 0;">{mat} <span style="color:#3b82f6;">({reg})</span></h2>',
        unsafe_allow_html=True,
    )
    cost_heads = display_module1(st.session_state["result_m1"], mat, reg)

    if st.session_state["result_m2"]:
        display_module2(st.session_state["result_m2"], mat, reg, p.get("periods", 3))

    if st.session_state["result_m3"]:
        display_module3(st.session_state["result_m3"], mat, reg)

    # Excel export block
    with st.expander("📋 Copy-paste output for Excel"):
        m1 = st.session_state["result_m1"]
        m3 = st.session_state["result_m3"]
        ch_str = " | ".join(
            f'{c["name"]} {c["weight_pct"]}%' for c in m1.get("cost_heads", [])
        )
        row = (
            f'{mat}\t{reg}\t'
            f'{m3.get("current_supply_risk","") if m3 else ""}\t'
            f'{m3.get("forecasted_supply_risk","") if m3 else ""}\t'
            f'{ch_str}\t'
            f'{m1["freshness"].get("confidence_level","")}\t'
            f'{TODAY_STR}\tTBC'
        )
        st.code(row, language=None)

elif not analyse_btn:
    st.markdown(
        '<div style="text-align:center;padding:80px 24px;color:#374151;">'
        '<div style="font-size:2rem;margin-bottom:12px;">⬡</div>'
        '<div style="font-size:1rem;color:#4b5563;">Select a material and region in the sidebar,<br>'
        'choose your modules, and click <strong style="color:#93c5fd;">Run Analysis</strong>.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;margin-top:3rem;padding-top:1.5rem;'
    'border-top:1px solid #0f172a;font-size:0.68rem;color:#374151;line-height:2;">'
    '<div>CommodityPulse · Procurement Intelligence Platform</div>'
    '<div>Powered by Anthropic Claude with live web search · Built for procurement teams</div>'
    '</div>',
    unsafe_allow_html=True,
)
