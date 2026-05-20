import streamlit as st
import anthropic
import pandas as pd
from datetime import datetime, date

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CommodityPulse – Procurement Intelligence",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAX_QUERIES = 2

DEFAULT_MATERIALS = sorted([
    "Aluminium Cans", "Aluminium Foil", "Aluminium Sheet", "Caustic Soda",
    "Cement", "Chlorine", "Cocoa Butter", "Copper Wire", "Corrugated Board",
    "Cotton Yarn", "Diesel Fuel", "Electricity (Industrial)", "Ethanol",
    "Flat Glass", "Flexible Packaging Film", "Float Glass", "Glass Bottles",
    "HDPE Resin", "Kraft Paper", "Labels & Sleeves", "LDPE Film",
    "Logistics - Air Freight", "Logistics - Road Freight", "Logistics - Sea Freight",
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

# ── Tool schemas (Anthropic generates guaranteed-valid JSON for these) ─────────

TOOL_MODULE1 = {
    "name": "output_cost_analysis",
    "description": "Output the structured cost head analysis result.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scope_note": {"type": "string", "description": "One sentence on data availability and proxy usage."},
            "freshness": {
                "type": "object",
                "properties": {
                    "check_date":             {"type": "string"},
                    "region":                 {"type": "string"},
                    "tax_basis":              {"type": "string"},
                    "primary_benchmarks":     {"type": "string"},
                    "most_recent_source_date":{"type": "string"},
                    "confidence_level":       {"type": "string", "enum": ["High", "Medium", "Low"]},
                    "narrative":              {"type": "string"}
                },
                "required": ["check_date","region","tax_basis","primary_benchmarks",
                             "most_recent_source_date","confidence_level","narrative"]
            },
            "cost_heads": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name":           {"type": "string"},
                        "weight_pct":     {"type": "number"},
                        "why_included":   {"type": "string"},
                        "best_fit_index": {"type": "string"},
                        "why_index":      {"type": "string"},
                        "is_proxy":       {"type": "boolean"}
                    },
                    "required": ["name","weight_pct","why_included","best_fit_index","why_index","is_proxy"]
                },
                "minItems": 4,
                "maxItems": 6
            }
        },
        "required": ["scope_note","freshness","cost_heads"]
    }
}

TOOL_MODULE2 = {
    "name": "output_inflation_analysis",
    "description": "Output the structured inflation impact projection.",
    "input_schema": {
        "type": "object",
        "properties": {
            "analysis_basis":  {"type": "string"},
            "key_assumptions": {"type": "string"},
            "disclaimer":      {"type": "string"},
            "months": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label":             {"type": "string"},
                        "weighted_total_pct":{"type": "number"},
                        "key_driver":        {"type": "string"},
                        "cost_head_impacts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name":                 {"type": "string"},
                                    "weight_pct":           {"type": "number"},
                                    "projected_change_pct": {"type": "number"},
                                    "direction":            {"type": "string", "enum": ["up","down","stable"]},
                                    "driver":               {"type": "string"}
                                },
                                "required": ["name","weight_pct","projected_change_pct","direction","driver"]
                            }
                        }
                    },
                    "required": ["label","weighted_total_pct","key_driver","cost_head_impacts"]
                }
            }
        },
        "required": ["analysis_basis","key_assumptions","disclaimer","months"]
    }
}

TOOL_MODULE3 = {
    "name": "output_shortage_tracker",
    "description": "Output the structured supply shortage tracker analysis.",
    "input_schema": {
        "type": "object",
        "properties": {
            "current_supply_risk":   {"type": "integer", "enum": [15, 45, 70, 98]},
            "forecasted_supply_risk":{"type": "integer", "enum": [15, 45, 70, 98]},
            "forecast_6m":           {"type": "string"},
            "forecast_12m_best":     {"type": "string"},
            "forecast_12m_base":     {"type": "string"},
            "forecast_12m_worst":    {"type": "string"},
            "variables": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "body":  {"type": "string"}
                    },
                    "required": ["title","body"]
                },
                "minItems": 4,
                "maxItems": 6
            },
            "additional_comments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title":      {"type": "string"},
                        "body":       {"type": "string"},
                        "references": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["title","body","references"]
                },
                "minItems": 3,
                "maxItems": 4
            },
            "all_references": {"type": "array", "items": {"type": "string"}}
        },
        "required": [
            "current_supply_risk","forecasted_supply_risk",
            "forecast_6m","forecast_12m_best","forecast_12m_base","forecast_12m_worst",
            "variables","additional_comments","all_references"
        ]
    }
}


# ── Helper utilities ──────────────────────────────────────────────────────────

def today_str():
    return datetime.today().strftime("%d %B %Y")


def get_api_key():
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        st.error(
            "API key not configured. "
            "Go to Streamlit Cloud > Settings > Secrets and add: "
            'ANTHROPIC_API_KEY = "sk-ant-..."'
        )
        st.stop()


def load_materials():
    try:
        df = pd.read_excel("materials.xlsx")
        for col in ["Material","material","L3 Category","Category","Service","Name"]:
            if col in df.columns:
                items = df[col].dropna().astype(str).str.strip().tolist()
                items = [i for i in items if i]
                if items:
                    return sorted(items)
        col0 = df.iloc[:,0].dropna().astype(str).str.strip().tolist()
        return sorted([i for i in col0 if i]) or DEFAULT_MATERIALS
    except Exception:
        return DEFAULT_MATERIALS


def snap_risk(score):
    try:
        score = int(float(score))
    except Exception:
        return 45
    return min(VALID_SCORES, key=lambda x: abs(x - score))


def risk_badge_html(score):
    score = snap_risk(score)
    label, color, bg, border = RISK_CFG[score]
    return (f'<span class="risk-badge" '
            f'style="color:{color};background:{bg};border:1.5px solid {border};">'
            f'● {score} — {label}</span>')


def conf_class(level):
    l = str(level).lower()
    if "high" in l: return "conf-high"
    if "low"  in l: return "conf-low"
    return "conf-med"


def month_labels(n):
    d = date.today()
    labels = []
    for _ in range(n):
        month = d.month % 12 + 1
        year  = d.year + (1 if d.month == 12 else 0)
        d = d.replace(year=year, month=month, day=1)
        labels.append(d.strftime("%B %Y"))
    return labels


def extract_all_text(response):
    return "\n\n".join(
        b.text.strip() for b in response.content
        if hasattr(b, "type") and b.type == "text"
    )


def extract_tool_result(response, tool_name):
    """Extract the input dict from a forced tool_use response. Always valid."""
    for b in response.content:
        if hasattr(b, "type") and b.type == "tool_use" and b.name == tool_name:
            return b.input
    raise ValueError(
        f"Model did not call the '{tool_name}' tool. "
        "Response content: " + str([getattr(b,"type","?") for b in response.content])
    )


# ── Two-step API calls ────────────────────────────────────────────────────────

def _research(client, prompt):
    """Step 1: Web-search enabled, returns plain-text research notes."""
    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    return extract_all_text(resp)


def _structure(client, research_text, tool_def, context_prompt):
    """Step 2: Force tool_use → Anthropic guarantees valid JSON. No web search."""
    tool_name = tool_def["name"]
    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        tools=[tool_def],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[{
            "role": "user",
            "content": (
                f"Research notes:\n\n{research_text}\n\n"
                f"{context_prompt}\n\n"
                f"Call the {tool_name} tool now with the structured output."
            )
        }],
    )
    return extract_tool_result(resp, tool_name)


# ── Module runners ────────────────────────────────────────────────────────────

def run_module1(material, region, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    today  = today_str()

    research = _research(client,
        f"You are a senior procurement cost analyst. Today is {today}.\n"
        f"Research the cost structure for: {material} in {region}.\n"
        f"Identify 4-6 cost heads (e.g. Energy, Raw Materials, Labour, Logistics, Conversion) "
        f"with approximate weight percentages summing to 100%.\n"
        f"For each cost head find the best public benchmark index or proxy available in {region}.\n"
        f"Find the most recent data dates for each benchmark.\n"
        f"Note the overall confidence level (High/Medium/Low) based on data availability.\n"
        f"Note the applicable tax/delivery basis for {region} (e.g. Duty Paid Rotterdam).\n"
        f"Be specific: include index names, issuing bodies, and most recent data dates."
    )

    return _structure(client, research, TOOL_MODULE1,
        f"Structure the above research for {material} in {region}. "
        f"Set check_date to '{today}'. Weights must sum to 100."
    )


def run_module2(material, region, periods, cost_heads, api_key):
    client  = anthropic.Anthropic(api_key=api_key)
    today   = today_str()
    labels  = month_labels(periods)
    ch_list = ", ".join(f"{c['name']} ({c['weight_pct']}%)" for c in cost_heads)

    research = _research(client,
        f"You are a senior procurement cost analyst. Today is {today}.\n"
        f"Research forward price signals for: {material} in {region}.\n"
        f"Cost heads to cover: {ch_list}\n"
        f"Months to project: {', '.join(labels)}\n"
        f"Find the latest futures curves, forward price data, and analyst forecasts "
        f"for each cost head benchmark in {region}.\n"
        f"For each month and each cost head, estimate the percentage change vs current levels.\n"
        f"Positive = cost increase. Negative = cost decrease.\n"
        f"Provide specific data points: actual futures levels or consensus ranges."
    )

    return _structure(client, research, TOOL_MODULE2,
        f"Structure the research for {material} in {region}. "
        f"Include exactly these months: {labels}. "
        f"weighted_total_pct for each month = sum of (projected_change_pct * weight_pct / 100). "
        f"Set disclaimer to: Estimate based on public forward signals as of {today}. Not a financial model."
    )


def run_module3(material, region, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    today  = today_str()

    research = _research(client,
        f"You are a senior procurement supply risk analyst. Today is {today}.\n"
        f"Research the current supply risk for: {material} in {region}.\n"
        f"Search for the latest data on:\n"
        f"- Production issues, plant shutdowns, capacity changes\n"
        f"- Trade flows, import dependence, export restrictions, sanctions\n"
        f"- Logistics constraints, freight rates, port disruptions\n"
        f"- Geopolitical risks and policy changes affecting supply\n"
        f"- Energy input costs and carbon compliance costs\n"
        f"- Weather or seasonal impacts on availability\n"
        f"- Downstream L3 category impacts and buyer exposure\n"
        f"Provide a 6-month availability outlook and 12-month best/base/worst scenarios.\n"
        f"Identify 3-4 specific buyer watchpoints or concentration risks.\n"
        f"Include URLs of all sources consulted. Focus entirely on {region}."
    )

    return _structure(client, research, TOOL_MODULE3,
        f"Structure the supply risk research for {material} in {region}. "
        f"Assign current_supply_risk and forecasted_supply_risk using only: 15, 45, 70, or 98. "
        f"15 = least risk, 98 = highest risk. "
        f"Include real source URLs in references fields."
    )


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;background:#080d16;color:#e5e7eb;}
.stApp{background:#080d16;}
.block-container{max-width:1100px;padding-top:1.5rem;padding-bottom:4rem;}
h1,h2,h3{font-family:'DM Sans',sans-serif;color:#f9fafb;}
#MainMenu,footer,header{visibility:hidden;}
.topbar{display:flex;justify-content:space-between;align-items:center;padding:12px 20px;
  background:linear-gradient(90deg,#0f172a,#0a1628);border-bottom:1px solid #1e3a5f;
  border-radius:10px;margin-bottom:1.5rem;}
.brand-name{font-weight:700;font-size:1rem;color:#f9fafb;}
.brand-sub{font-size:0.62rem;color:#4b5563;letter-spacing:0.1em;}
.date-pill{font-size:0.68rem;color:#4b5563;letter-spacing:0.08em;
  background:rgba(59,130,246,0.08);border:1px solid #1e3a5f;
  border-radius:6px;padding:4px 10px;font-family:'DM Mono',monospace;}
.card{background:linear-gradient(135deg,#0f172a,#111827);border:1px solid #1e3a5f;
  border-radius:14px;padding:22px;margin-bottom:16px;box-shadow:0 4px 24px rgba(0,0,0,0.4);}
.card-warn{border-color:rgba(250,204,21,0.3)!important;}
.slabel{font-size:0.62rem;font-weight:700;color:#6b7280;letter-spacing:0.12em;
  text-transform:uppercase;margin-bottom:10px;font-family:'DM Mono',monospace;}
.risk-badge{display:inline-block;border-radius:6px;padding:5px 14px;font-weight:700;
  font-size:0.78rem;letter-spacing:0.06em;font-family:'DM Mono',monospace;}
.module-header{font-size:0.72rem;font-weight:700;color:#3b82f6;letter-spacing:0.15em;
  text-transform:uppercase;margin-bottom:4px;font-family:'DM Mono',monospace;}
.module-title{font-size:1.15rem;font-weight:700;color:#f9fafb;margin-bottom:16px;}
.ft-table{width:100%;border-collapse:collapse;font-size:0.82rem;}
.ft-table th{background:#0f172a;color:#6b7280;font-size:0.62rem;letter-spacing:0.1em;
  text-transform:uppercase;padding:8px 12px;border-bottom:1px solid #1e3a5f;
  font-family:'DM Mono',monospace;text-align:left;}
.ft-table td{padding:9px 12px;border-bottom:1px solid #0f172a;color:#d1d5db;vertical-align:top;}
.ft-table tr:last-child td{border-bottom:none;}
.ft-key{color:#93c5fd;font-family:'DM Mono',monospace;font-size:0.78rem;white-space:nowrap;}
.ch-table{width:100%;border-collapse:collapse;font-size:0.8rem;}
.ch-table th{background:#0a1121;color:#6b7280;font-size:0.6rem;letter-spacing:0.1em;
  text-transform:uppercase;padding:9px 12px;border-bottom:2px solid #1e3a5f;
  font-family:'DM Mono',monospace;text-align:left;}
.ch-table td{padding:9px 12px;border-bottom:1px solid #0f172a;color:#d1d5db;vertical-align:top;line-height:1.55;}
.ch-table tr:last-child td{border-bottom:none;}
.weight-pill{display:inline-block;background:rgba(59,130,246,0.15);
  border:1px solid rgba(59,130,246,0.4);border-radius:20px;padding:2px 9px;
  font-weight:700;color:#93c5fd;font-family:'DM Mono',monospace;font-size:0.78rem;}
.proxy-tag{display:inline-block;background:rgba(250,204,21,0.1);
  border:1px solid rgba(250,204,21,0.3);border-radius:4px;padding:1px 6px;
  font-size:0.68rem;color:#fde68a;font-family:'DM Mono',monospace;margin-left:4px;}
.inf-table{width:100%;border-collapse:collapse;font-size:0.8rem;}
.inf-table th{background:#0a1121;color:#6b7280;font-size:0.6rem;letter-spacing:0.1em;
  text-transform:uppercase;padding:8px 12px;border-bottom:2px solid #1e3a5f;
  font-family:'DM Mono',monospace;text-align:left;}
.inf-table td{padding:9px 12px;border-bottom:1px solid #0f172a;color:#d1d5db;vertical-align:top;}
.inf-table tr:last-child td{border-bottom:none;}
.inf-pos{color:#f97316;font-weight:700;font-family:'DM Mono',monospace;}
.inf-neg{color:#22c55e;font-weight:700;font-family:'DM Mono',monospace;}
.inf-neu{color:#facc15;font-weight:700;font-family:'DM Mono',monospace;}
.inf-total{background:rgba(59,130,246,0.08)!important;font-weight:700;}
.bullet-block{border-left:2px solid #1e3a5f;padding:10px 14px;margin-bottom:10px;
  border-radius:0 6px 6px 0;background:rgba(255,255,255,0.02);}
.bullet-title{color:#93c5fd;font-weight:600;font-size:0.84rem;}
.bullet-body{color:#d1d5db;font-size:0.82rem;line-height:1.65;margin-top:4px;}
.scenario-best{border-left:3px solid #22c55e;padding:10px 14px;background:rgba(34,197,94,0.04);border-radius:0 8px 8px 0;margin-bottom:8px;}
.scenario-base{border-left:3px solid #facc15;padding:10px 14px;background:rgba(250,204,21,0.04);border-radius:0 8px 8px 0;margin-bottom:8px;}
.scenario-worst{border-left:3px solid #ef4444;padding:10px 14px;background:rgba(239,68,68,0.04);border-radius:0 8px 8px 0;margin-bottom:8px;}
.sc-label{font-size:0.62rem;font-weight:700;letter-spacing:0.1em;margin-bottom:4px;font-family:'DM Mono',monospace;}
.sc-text{font-size:0.82rem;color:#d1d5db;line-height:1.6;}
.scope-note{background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.2);
  border-radius:8px;padding:12px 16px;font-size:0.8rem;color:#93c5fd;line-height:1.6;margin-bottom:16px;}
.conf-high{color:#22c55e;font-weight:700;}
.conf-med{color:#facc15;font-weight:700;}
.conf-low{color:#f97316;font-weight:700;}
.ref-link{font-size:0.7rem;color:#3b82f6;word-break:break-all;line-height:1.9;font-family:'DM Mono',monospace;}
div[data-testid="stButton"] button{
  background:linear-gradient(135deg,#1d4ed8,#2563eb);color:#fff;font-weight:700;
  border:none;border-radius:10px;padding:0.55rem 2rem;
  font-family:'DM Sans',sans-serif;font-size:0.9rem;letter-spacing:0.04em;}
div[data-testid="stButton"] button:hover{
  background:linear-gradient(135deg,#2563eb,#3b82f6);
  box-shadow:0 0 20px rgba(59,130,246,0.3);}
</style>
""", unsafe_allow_html=True)


# ── Display functions ─────────────────────────────────────────────────────────

def display_module1(d, material, region):
    f  = d.get("freshness", {})
    ch = d.get("cost_heads", [])

    st.markdown('<div class="module-header">MODULE 1</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-title">Cost Head Analysis</div>', unsafe_allow_html=True)

    if d.get("scope_note"):
        st.markdown(
            f'<div class="scope-note">{material} ({region}) — {d["scope_note"]}</div>',
            unsafe_allow_html=True)

    st.markdown('<div class="slabel">B. Freshness Block</div>', unsafe_allow_html=True)
    conf = f.get("confidence_level", "Medium")
    rows = "".join([
        f'<tr><td class="ft-key">Market status check date</td><td>{f.get("check_date", today_str())}</td></tr>',
        f'<tr><td class="ft-key">Region</td><td>{f.get("region", region)}</td></tr>',
        f'<tr><td class="ft-key">Tax basis</td><td>{f.get("tax_basis","N/A")}</td></tr>',
        f'<tr><td class="ft-key">Primary benchmark(s) used</td><td>{f.get("primary_benchmarks","-")}</td></tr>',
        f'<tr><td class="ft-key">Most recent source date found</td><td>{f.get("most_recent_source_date","-")}</td></tr>',
        f'<tr><td class="ft-key">Confidence level</td>'
        f'<td><span class="{conf_class(conf)}">{conf}</span></td></tr>',
    ])
    st.markdown(
        f'<div class="card"><table class="ft-table"><thead><tr><th>Item</th><th>Value</th>'
        f'</tr></thead><tbody>{rows}</tbody></table></div>',
        unsafe_allow_html=True)
    if f.get("narrative"):
        st.markdown(
            f'<div class="card" style="padding:14px 20px;">'
            f'<div style="font-size:0.82rem;color:#d1d5db;line-height:1.7;">{f["narrative"]}</div></div>',
            unsafe_allow_html=True)

    st.markdown('<div class="slabel" style="margin-top:16px;">C. Cost-Head Table</div>',
                unsafe_allow_html=True)
    ch_rows = ""
    for c in ch:
        proxy = '<span class="proxy-tag">PROXY</span>' if c.get("is_proxy") else ""
        ch_rows += (
            f'<tr><td><strong style="color:#f9fafb;">{c.get("name","")}</strong></td>'
            f'<td><span class="weight-pill">{c.get("weight_pct",0)}%</span></td>'
            f'<td>{c.get("why_included","")}</td>'
            f'<td>{c.get("best_fit_index","")}{proxy}</td>'
            f'<td>{c.get("why_index","")}</td></tr>'
        )
    st.markdown(
        f'<div class="card"><table class="ch-table"><thead><tr>'
        f'<th>Cost Head</th><th>Weight %</th><th>Why Included</th>'
        f'<th>Best-Fit Index / Proxy</th><th>Why This Index</th>'
        f'</tr></thead><tbody>{ch_rows}</tbody></table></div>',
        unsafe_allow_html=True)
    return ch


def display_module2(d):
    st.markdown('<hr style="border:none;border-top:1px solid #1e3a5f;margin:20px 0;">',
                unsafe_allow_html=True)
    st.markdown('<div class="module-header">MODULE 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-title">Inflation Impact Projection</div>', unsafe_allow_html=True)

    if d.get("analysis_basis"):
        st.markdown(f'<div class="scope-note">{d["analysis_basis"]}</div>', unsafe_allow_html=True)

    months = d.get("months", [])
    if months:
        heads  = [h.get("name","") for h in months[0].get("cost_head_impacts",[])]
        header = "<tr><th>Month</th>" + "".join(f"<th>{h}</th>" for h in heads) + "<th>Weighted Total</th><th>Key Driver</th></tr>"
        rows   = ""
        for m in months:
            cells = ""
            for imp in m.get("cost_head_impacts",[]):
                try:    pct = float(imp.get("projected_change_pct",0))
                except: pct = 0.0
                css  = "inf-pos" if pct > 0 else ("inf-neg" if pct < 0 else "inf-neu")
                sign = "+" if pct > 0 else ""
                cells += (f'<td class="{css}">{sign}{pct:.1f}%<br>'
                          f'<span style="font-size:0.68rem;color:#6b7280;font-weight:400;">'
                          f'{imp.get("driver","")}</span></td>')
            try:    total = float(m.get("weighted_total_pct",0))
            except: total = 0.0
            t_css = "inf-pos" if total > 0 else ("inf-neg" if total < 0 else "inf-neu")
            sign  = "+" if total > 0 else ""
            rows += (f'<tr><td style="color:#f9fafb;font-weight:600;white-space:nowrap;">'
                     f'{m.get("label","")}</td>{cells}'
                     f'<td class="inf-total {t_css}">{sign}{total:.2f}%</td>'
                     f'<td style="font-size:0.78rem;color:#d1d5db;">{m.get("key_driver","")}</td></tr>')
        st.markdown(
            f'<div class="card" style="overflow-x:auto;">'
            f'<table class="inf-table"><thead>{header}</thead><tbody>{rows}</tbody></table></div>',
            unsafe_allow_html=True)

    if d.get("key_assumptions"):
        st.markdown(
            f'<div class="card card-warn"><div class="slabel">Key Assumptions</div>'
            f'<div style="font-size:0.82rem;color:#d1d5db;line-height:1.7;">{d["key_assumptions"]}</div></div>',
            unsafe_allow_html=True)
    if d.get("disclaimer"):
        st.markdown(
            f'<div style="font-size:0.72rem;color:#4b5563;margin-top:6px;">&#9888; {d["disclaimer"]}</div>',
            unsafe_allow_html=True)


def display_module3(d):
    st.markdown('<hr style="border:none;border-top:1px solid #1e3a5f;margin:20px 0;">',
                unsafe_allow_html=True)
    st.markdown('<div class="module-header">MODULE 3</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-title">Shortage Tracker</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<div class="card"><div class="slabel">Current Supply Risk</div>'
            f'{risk_badge_html(d.get("current_supply_risk",45))}</div>',
            unsafe_allow_html=True)
    with col2:
        st.markdown(
            f'<div class="card"><div class="slabel">Forecasted Supply Risk</div>'
            f'{risk_badge_html(d.get("forecasted_supply_risk",45))}</div>',
            unsafe_allow_html=True)

    if d.get("variables"):
        st.markdown('<div class="slabel" style="margin-top:8px;">Variables Impacting Availability</div>',
                    unsafe_allow_html=True)
        html = '<div class="card">'
        for v in d["variables"]:
            html += (f'<div class="bullet-block">'
                     f'<div class="bullet-title">&gt; {v.get("title","")}</div>'
                     f'<div class="bullet-body">{v.get("body","")}</div></div>')
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    st.markdown('<div class="slabel" style="margin-top:4px;">Availability Forecast</div>',
                unsafe_allow_html=True)
    st.markdown(
        f'<div class="card">'
        f'<div class="slabel" style="color:#4b5563;">6-Month Outlook</div>'
        f'<div style="font-size:0.82rem;color:#d1d5db;line-height:1.7;margin-bottom:16px;">'
        f'&gt; {d.get("forecast_6m","")}</div>'
        f'<div class="slabel" style="color:#4b5563;">12-Month Scenarios</div>'
        f'<div class="scenario-best"><div class="sc-label" style="color:#22c55e;">&#9650; BEST CASE</div>'
        f'<div class="sc-text">{d.get("forecast_12m_best","")}</div></div>'
        f'<div class="scenario-base"><div class="sc-label" style="color:#facc15;">&#9670; BASE CASE</div>'
        f'<div class="sc-text">{d.get("forecast_12m_base","")}</div></div>'
        f'<div class="scenario-worst"><div class="sc-label" style="color:#ef4444;">&#9660; WORST CASE</div>'
        f'<div class="sc-text">{d.get("forecast_12m_worst","")}</div></div></div>',
        unsafe_allow_html=True)

    if d.get("additional_comments"):
        st.markdown('<div class="slabel" style="margin-top:4px;">Additional Comments</div>',
                    unsafe_allow_html=True)
        html = '<div class="card">'
        for c in d["additional_comments"]:
            refs = "".join(
                f'<a href="{r}" target="_blank" class="ref-link">{r}</a><br>'
                for r in c.get("references",[])
            )
            html += (f'<div class="bullet-block">'
                     f'<div class="bullet-title">&gt; {c.get("title","")}</div>'
                     f'<div class="bullet-body">{c.get("body","")}</div>'
                     f'{"<div style=margin-top:6px;>" + refs + "</div>" if refs else ""}'
                     f'</div>')
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    if d.get("all_references"):
        with st.expander("All References"):
            for r in d["all_references"]:
                st.markdown(f'<a href="{r}" target="_blank" class="ref-link">{r}</a>',
                            unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {"query_count": 0, "result_m1": None,
             "result_m2": None, "result_m3": None, "last_params": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

materials_list = load_materials()

# ── Top bar ───────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="topbar">'
    f'<div><div class="brand-name">&#11203; CommodityPulse</div>'
    f'<div class="brand-sub">PROCUREMENT INTELLIGENCE PLATFORM</div></div>'
    f'<div class="date-pill">ANALYSIS DATE: {datetime.today().strftime("%d %b %Y").upper()}</div>'
    f'</div>',
    unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Analysis Parameters")
    st.markdown("---")
    selected_material = st.selectbox("Select L3 Category / Material", options=materials_list)
    selected_region   = st.selectbox("Region",
        options=["Europe","North America","Asia Pacific","Middle East & Africa","Latin America"],
        index=0)
    st.markdown("---")
    st.markdown("**Select Analysis Modules**")
    run_m2 = st.checkbox("Module 2 — Inflation Impact", value=False)
    run_m3 = st.checkbox("Module 3 — Shortage Tracker", value=False)
    forecast_periods = 3
    if run_m2:
        forecast_periods = st.select_slider("Forecast period (months)",
                                            options=[1,2,3,4,5,6], value=3)
    st.markdown("---")
    queries_left = MAX_QUERIES - st.session_state["query_count"]
    if queries_left > 0:
        st.markdown(
            f'<div style="font-size:0.72rem;color:#6b7280;font-family:\'DM Mono\',monospace;">'
            f'Trial queries remaining: <strong style="color:#f9fafb;">{queries_left} / {MAX_QUERIES}</strong></div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="font-size:0.72rem;color:#ef4444;">Trial limit reached.</div>',
            unsafe_allow_html=True)
    analyse_btn = st.button("Run Analysis →", use_container_width=True, disabled=(queries_left <= 0))
    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.68rem;color:#374151;line-height:1.9;">'
        'Module 1 always runs.<br>Module 2 uses Module 1 cost heads.<br>'
        'Module 3 fetches live supply data.<br><br>'
        '&#9888; AI-generated estimates only.<br>Validate before decisions.</div>',
        unsafe_allow_html=True)

# ── Run analysis ──────────────────────────────────────────────────────────────
if analyse_btn:
    api_key = get_api_key()
    st.session_state.update({"query_count": st.session_state["query_count"] + 1,
                              "result_m1": None, "result_m2": None, "result_m3": None,
                              "last_params": {"material": selected_material,
                                              "region": selected_region,
                                              "run_m2": run_m2, "run_m3": run_m3,
                                              "periods": forecast_periods}})
    with st.spinner(f"Module 1 — Researching cost structure for {selected_material}..."):
        try:
            st.session_state["result_m1"] = run_module1(selected_material, selected_region, api_key)
        except Exception as e:
            st.error(f"Module 1 error: {e}")

    if run_m2 and st.session_state["result_m1"]:
        with st.spinner(f"Module 2 — Projecting inflation impact over {forecast_periods} months..."):
            try:
                st.session_state["result_m2"] = run_module2(
                    selected_material, selected_region, forecast_periods,
                    st.session_state["result_m1"].get("cost_heads",[]), api_key)
            except Exception as e:
                st.error(f"Module 2 error: {e}")

    if run_m3:
        with st.spinner("Module 3 — Fetching live supply risk data..."):
            try:
                st.session_state["result_m3"] = run_module3(selected_material, selected_region, api_key)
            except Exception as e:
                st.error(f"Module 3 error: {e}")

# ── Display results ───────────────────────────────────────────────────────────
p   = st.session_state.get("last_params") or {}
mat = p.get("material","")
reg = p.get("region","Europe")

if st.session_state["result_m1"]:
    st.markdown(
        f'<div style="font-size:0.68rem;color:#6b7280;margin-bottom:4px;font-family:\'DM Mono\',monospace;">RESULTS FOR</div>'
        f'<h2 style="margin:0 0 20px 0;">{mat} <span style="color:#3b82f6;">({reg})</span></h2>',
        unsafe_allow_html=True)
    cost_heads = display_module1(st.session_state["result_m1"], mat, reg)
    if st.session_state["result_m2"]:
        display_module2(st.session_state["result_m2"])
    if st.session_state["result_m3"]:
        display_module3(st.session_state["result_m3"])
    with st.expander("Copy-paste output for Excel"):
        m1  = st.session_state["result_m1"]
        m3  = st.session_state["result_m3"]
        row = "\t".join([
            mat, reg,
            str(m3.get("current_supply_risk","")) if m3 else "",
            str(m3.get("forecasted_supply_risk","")) if m3 else "",
            " | ".join(f'{c["name"]} {c["weight_pct"]}%' for c in m1.get("cost_heads",[])),
            m1.get("freshness",{}).get("confidence_level",""),
            today_str(), "TBC"
        ])
        st.code(row, language=None)
elif not analyse_btn:
    st.markdown(
        '<div style="text-align:center;padding:80px 24px;color:#374151;">'
        '<div style="font-size:2rem;margin-bottom:12px;">&#11203;</div>'
        '<div style="font-size:1rem;color:#4b5563;">Select a material and region in the sidebar,<br>'
        'choose your modules, and click <strong style="color:#93c5fd;">Run Analysis</strong>.</div>'
        '</div>', unsafe_allow_html=True)

st.markdown(
    '<div style="text-align:center;margin-top:3rem;padding-top:1.5rem;'
    'border-top:1px solid #0f172a;font-size:0.68rem;color:#374151;line-height:2;">'
    'CommodityPulse &nbsp;·&nbsp; Procurement Intelligence Platform<br>'
    'Powered by Anthropic Claude with live web search</div>',
    unsafe_allow_html=True)
