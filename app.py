import streamlit as st
import anthropic
import plotly.graph_objects as go
from datetime import datetime, date

st.set_page_config(
    page_title="CommodityPulse",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 349 L3 categories ─────────────────────────────────────────────────────────
CATEGORIES = [
    "CARPENTER (BUILDING MATERIALS)","CEILING (BUILDING MATERIALS)","COOLING (BUILDING MATERIALS)",
    "DOORS (BUILDING MATERIALS)","ELECTRICITY HV (BUILDING MATERIALS)","ELECTRICITY LV (BUILDING MATERIALS)",
    "ELEVATORS (BUILDING MATERIALS)","EMERGENCY GENERATORS & UPS (NO-BREAK) (BUILDING MATERIALS)",
    "FLOOR LAYER (BUILDING MATERIALS)","HVAC (BUILDING MATERIALS)","LIGHTING INDOOR (BUILDING MATERIALS)",
    "LIGHTING OUTDOOR (BUILDING MATERIALS)","OTHER (BUILDING MATERIALS)","PAINTER (BUILDING MATERIALS)",
    "PLUMBER/SEWER (BUILDING MATERIALS)","ADVISORY SERVICES","ARCHITECT","CARCASE WORKS",
    "CARPENTER (CONTRACTORS)","CEILING (CONTRACTORS)","COOLING (CONTRACTORS)","COORDINATION",
    "DATA CABLES","DEMOLITION","DOORS (CONTRACTORS)","ELECTRICITY HV (CONTRACTORS)",
    "ELECTRICITY LV (CONTRACTORS)","ELEVATORS (CONTRACTORS)",
    "EMERGENCY GENERATORS & UPS (NO-BREAK) (CONTRACTORS)","ENGINEERING",
    "FIRE SAFETY (CONTRACTORS)","FLOOR LAYER (CONTRACTORS)","GENERAL CONTRACTORS",
    "HVAC (CONTRACTORS)","INFRASTRUCTURE OUTSOURCING SERVICES (CONTRACTORS)","OTHER (CONTRACTORS)",
    "PAINTER (CONTRACTORS)","PLUMBER/SEWER (CONTRACTORS)","ROOF WORK","SECURITY SYSTEM",
    "SHELVING (CONTRACTORS)","SIGNING (CONTRACTORS)",
    "BUILDINGS / COLD SHELL (EXTERIOR REAL ESTATE)","BUILDINGS / HOT SHELL (INTERIOR FORMAT BASED)",
    "COOLING (MAINTENANCE)","ELECTRICITY HV (MAINTENANCE)","ELECTRICITY LV (MAINTENANCE)",
    "ELEVATORS (MAINTENANCE)","EMERGENCY GENERATORS & UPS (NO-BREAK) (MAINTENANCE)",
    "FIRE SAFETY (MAINTENANCE)","GROUNDS / SURROUNDINGS (F.E. PARKING FACILITIES)",
    "HVAC (MAINTENANCE)","LIGHTING INDOOR (MAINTENANCE)","LIGHTING OUTDOOR (MAINTENANCE)",
    "OTHER (MAINTENANCE)","PLUMBER/SEWER (MAINTENANCE)","WATER TREATMENT / SANITARY",
    "SITE LEASE FOR STORES & PARKING","SITE PURCHASES AND SALES FOR STORES & PARKING",
    "CREATIVE/DIGITAL CONSULTANCY","IT CONSULTANCY","LEGAL CONSULTANCY","MANAGEMENT CONSULTANCY",
    "MEMBERSHIPS & SPONSORING (NON MARKETING)","QUALITY TESTING/CERTIFICATION",
    "STRATEGY CONSULTANCY","SUPPLY CHAIN CONSULTANCY","TAX CONSULTANCY",
    "OTHER (EXTERNAL HIRING)","TEMP LABOR FOR STORES","TEMP LABOR FOR WAREHOUSES",
    "FINANCE & ACCOUNTING SERVICES","FINANCIAL AUDIT SERVICES","GENERAL BANKING SERVICES",
    "INSURANCES","LEASING (EMPLOYEE CARS/VANS)","MONEY HANDLING AND TRANSPORT",
    "PAYMENT TRANSACTION FEES","ADMINISTRATIVE PAYROLL","EMPLOYEE BENEFITS","HEALTH SERVICES",
    "LEARNING & DEVELOPMENT","OTHER MOBILITY SOLUTIONS","OUTPLACEMENT","RECRUITMENT SERVICES",
    "AIRLINE TICKETS","BOOKING AGENCIES AND TOOLS","EVENTS (TRAVEL & EVENTS)",
    "EXTERNAL LOCATIONS","HOTEL (NIGHTS)","OTHER TRANSPORT (NON COMMUTING)",
    "CABINETS PLUG-IN (COOLING)","CABINETS REMOTE (COOLING)","OTHER (COOLING)",
    "FURNITURE MIXED MATERIALS","FURNITURE/FIXTURES BACK OFFICE, HQ, CANTEEN (FURNITURE)",
    "FURNITURE/FIXTURES STORE CASH WRAPS/CHECKOUTS (FURNITURE)",
    "FURNITURE/FIXTURES STORE INOX/STEEL (FURNITURE)","FURNITURE/FIXTURES STORE PLASTIC",
    "FURNITURE/FIXTURES STORE WOOD (FURNITURE)","OTHER (FURNITURE)","SHELVING (FURNITURE)",
    "(SHELL)FISH PROCESSING MACHINES (MACHINERY)","AUDIO/SOUND EQUIPMENT (MACHINERY)",
    "BREAD PROCESSING MACHINES (MACHINERY)","CHEESE PROCESSING MACHINES (MACHINERY)",
    "CLEANING MACHINES/CLEANING DISPENSER (MACHINERY)","COFFEE MACHINES (MACHINERY)",
    "DELI EQUIPMENT & UTENSILS (MACHINERY)","FRUIT & VEG PROCESSING MACHINES (MACHINERY)",
    "GRILLS (MACHINERY)","MEAT PROCESSING MACHINES (MACHINERY)","OTHER (MACHINERY)",
    "OVENS (MACHINERY)","PACKING MACHINE (MACHINERY)","PAPER PROCESSING MACHINES (MACHINERY)",
    "REVERSE VENDING MACHINES (MACHINERY)","VENDING MACHINES (MACHINERY)",
    "WEIGHING EQUIPMENT (MACHINERY)","CABINETS PLUG-IN (MAINTENANCE COOLING)",
    "CABINETS REMOTE (MAINTENANCE COOLING)","OTHER (MAINTENANCE COOLING)",
    "FURNITURE/FIXTURES BACK OFFICE, HQ, CANTEEN (MAINTENANCE FURNITURE)",
    "FURNITURE/FIXTURES STORE CASH WRAPS/CHECKOUTS (MAINTENANCE FURNITURE)",
    "FURNITURE/FIXTURES STORE INOX/STEEL (MAINTENANCE FURNITURE)",
    "FURNITURE/FIXTURES STORE PLASTIC (MAINTENANCE FURNITURE)",
    "FURNITURE/FIXTURES STORE WOOD (MAINTENANCE FURNITURE)","OTHER (MAINTENANCE FURNITURE)",
    "SHELVING (MAINTENANCE FURNITURE)","(SHELL)FISH PROCESSING MACHINES (MAINTENANCE MACHINERY)",
    "AUDIO/SOUND EQUIPMENT (MAINTENANCE MACHINERY)","BREAD PROCESSING MACHINES (MAINTENANCE MACHINERY)",
    "CHEESE PROCESSING MACHINES (MAINTENANCE MACHINERY)",
    "CLEANING MACHINES/CLEANING DISPENSER (MAINTENANCE MACHINERY)",
    "COFFEE MACHINES (MAINTENANCE MACHINERY)","DELI EQUIPMENT & UTENSILS (MAINTENANCE MACHINERY)",
    "FRUIT & VEG PROCESSING MACHINES (MAINTENANCE MACHINERY)","GRILLS (MAINTENANCE MACHINERY)",
    "MEAT PROCESSING MACHINES (MAINTENANCE MACHINERY)","OTHER (MAINTENANCE MACHINERY)",
    "OVENS (MAINTENANCE MACHINERY)","PACKING MACHINE (MAINTENANCE MACHINERY)",
    "PAPER PROCESSING MACHINES (MAINTENANCE MACHINERY)",
    "REVERSE VENDING MACHINES (MAINTENANCE MACHINERY)","VENDING MACHINES (MAINTENANCE MACHINERY)",
    "WEIGHING EQUIPMENT (MAINTENANCE MACHINERY)","OTHER (MAINTENANCE MERCHANDISING)",
    "SHELVING ACCESSORIES (MAINTENANCE MERCHANDISING)","SHOPPING BASKETS (MAINTENANCE MERCHANDISING)",
    "SHOPPING CARTS/TROLLEYS (MAINTENANCE MERCHANDISING)","SIGNING (MAINTENANCE MERCHANDISING)",
    "ENTRANCE BARRIERS & MECHANICS/SWING GATES (MAINTENANCE SECURITY)",
    "FIRE SAFETY (MAINTENANCE SECURITY)","OTHER (MAINTENANCE SECURITY)",
    "SAFE/MONEY HANDLING (MAINTENANCE SECURITY)","SECURITY SYSTEMS (MAINTENANCE SECURITY)",
    "TELETUBE CHECK OUT AIRBOXSYSTEM (MAINTENANCE SECURITY)","OTHER (MERCHANDISING)",
    "SHELVING ACCESSORIES (MERCHANDISING)","SHOPPING BASKETS (MERCHANDISING)",
    "SHOPPING CARTS/TROLLEYS (MERCHANDISING)","SIGNING (MERCHANDISING)",
    "ENTRANCE BARRIERS & MECHANICS/SWING GATES (SECURITY)","FIRE SAFETY (SECURITY)",
    "OTHER (SECURITY)","SAFE/MONEY HANDLING (SECURITY)","SECURITY SYSTEMS (SECURITY)",
    "TELETUBE CHECK OUT AIRBOXSYSTEM (SECURITY)","CATERING OFFICES/WAREHOUSES",
    "CLEANING & HYGIENE SERVICES","OFFICE CLEANING SERVICES","PEST CONTROL","QUALITY AUDITS",
    "SANITARY SERVICES","STORE CLEANING SERVICES","WAREHOUSE CLEANING","ARCHIVING",
    "OTHER FACILITY SUPPORT SERVICES","SURROUNDINGS SERVICES","FIRE PROTECTION SERVICES",
    "IN-STORE SECURITY","WAREHOUSE AND OFFICE SECURITY","DATACENTER HARDWARE",
    "INFRASTRUCTURE H/W - OTHERS","PRINTING HARDWARE","STORE EQUIPMENT - OTHERS",
    "STORE EQUIPMENT (ELECTRONIC SHELF LABELS)","STORE EQUIPMENT (HANDHELDS)",
    "STORE EQUIPMENT (SCALES)","IT","AMS TESTING SERVICES",
    "APPLICATION MAINTENANCE AND SUPPORT","APPLICATION PROJECT SERVICES",
    "DATA CENTER SERVICES (INFRASTRUCTURE)","DATA CENTER SERVICES (IT 3RD PARTY SERVICES)",
    "END USER COMPUTING","INFRASTRUCTURE OUTSOURCING SERVICES (IT 3RD PARTY SERVICES)",
    "IT BREAK/FIX SERVICES AND MAINTENANCE","OTHER (INFRASTRUCTURE PROJECT SERVICES)",
    "PAY CARDS","PEN TESTING","PRINTED SERVICES (IT)","TESTING AS A SERVICE",
    "EXTERNAL IT PERSONNEL","IT CONSULTING","IT HIRED SERVICES",
    "OTHER IT PROFESSIONAL SERVICES","LICENSE MANAGEMENT","SOFTWARE AS A SERVICE",
    "SOFTWARE LICENSE","SOFTWARE MAINTENANCE","CONFERENCING SERVICES","FIXED TELEPHONY",
    "MOBILE TELEPHONY","OTHER TELECOM SERVICES","TELECOM HARDWARE","WIDE AREA NETWORK",
    "OUTSOURCED AMBIENT","OUTSOURCED CUSTOMS BROKERS","OUTSOURCED E-COM","OUTSOURCED FRESH",
    "OUTSOURCED FROZEN","OUTSOURCED RETURNABLES","HOME DELIVERY TRANSPORT OPERATIONS",
    "INTERNATIONAL INBOUND TRANSPORT OPERATIONS - RAIL TRANSPORT",
    "INTERNATIONAL INBOUND TRANSPORT OPERATIONS - ROAD TRANSPORT",
    "INTERNATIONAL INBOUND TRANSPORT OPERATIONS - SEA TRANSPORT",
    "NATIONAL INBOUND TRANSPORT OPERATIONS","NATIONAL OUTBOUND TRANSPORT",
    "OWNED VEHICLES FLEET","OWNED VEHICLES MAINTENANCE","SMALL PARCELS",
    "BATTERIES FOR MATERIAL HANDLING EQUIPMENT","CRATES","MATERIAL HANDLING EQUIPMENT",
    "MATERIAL HANDLING EQUIPMENT MAINTENANCE","OTHER (WAREHOUSE INVENTORY)","PALLETS",
    "RACKING WAREHOUSE","ROLLING CARRIERS","MECHANIZATION SERVICE & MAINTENANCE",
    "MECHANIZATION SOLUTION","COMMUNICATIONS/ PR","CREATIVE EXECUTION",
    "LOCAL/ STORE EVENTS AND INSTORE ACTIVATIONS","LOYALTY","MONETIZATION",
    "OUTDOOR / INDOOR SIGNAGE","PACKAGING DESIGN","STRATEGIC","(VOICE) ACTORS",
    "FILM/VIDEO PRODUCTION","MUSIC INSTORE","PHOTOGRAPHY","AFFILIATE MARKETING",
    "DIGITAL SIGNAGE","ONLINE MARKETING","SOCIAL MEDIA","WEB & APPS DESIGN",
    "EVENTS (EVENTS)","CONSUMER INSIGHTS","MARKET INSIGHTS","MEDIA AGENCY","ONLINE",
    "OUT OF HOME","PRINT ADVERTISEMENT","RADIO","SEO AND SEA","TV","PUBLICATION PAPER",
    "PRINT MANAGEMENT","PRINT PRODUCTION","PRINT DISTRIBUTION",
    "PRINT DISTRIBUTION QUALITY CHECK","SPONSORING","DONATIONS","EMPLOYEES SOCIAL BENEFITS",
    "HR MEMBERSHIPS","WAGES","LAND DRAINING RATES","LOCAL TAXES","OTHER CHARGES & TAXES",
    "PENALTIES","PROPERTY TAXES","SEWAGE CHARGES","MEMBERSHIPS","INTER COMPANY",
    "FOR RESALE FUEL","INTERCOMPANY","TRADE / FOR RESALE (INTERCOMPANY)",
    "CHAMBER OF COMMERCE",
    "OTHER NGO (NON-GOVERNMENTAL ORGANIZATION) (NGO (NON-GOVERNMETAL ORGANIZATION))",
    "RETAILER ASSOCIATION FEE","NON-NFR","COLLECTION FEES","LEGAL FEES",
    "REAL ESTATE & CONSTRUCTION CHARGES","TRADE / FOR RESALE (NON-NFR SPEND)",
    "OTHER INCOME",
    "OTHER NGO (NON-GOVERNMENTAL ORGANIZATION) (OTHER NGO (NON-GOVERNMENTAL ORGANIZATION))",
    "QUOTATION STOCK EXCHANGE","BAKERY BAGS","BOTTLES & TUBES","CARTON BOXES","CUPS & LIDS",
    "FOILS","INSTORE BAGS AND NETS","LABELS & SLEEVES","PAPER WRAPS & RUBBERS",
    "TRAYS, BOWLS AND PLATTERS","(THERMAL) TILL ROLLS","CLEANING CHEMICALS/MATERIALS",
    "DISPOSABLES","DISTRIBUTION SUPPLIES","GENERAL SUPPLIES","INSTORE SUPPLY PAPER",
    "MEAT DEPT. SUPPLIES","NON-PLASTIC CARRIER BAGS (CHECK OUTS)","OFFICE SUPPLIES",
    "PAPER HYGIENE PRODUCTS","PLASTIC CARRIER BAGS (CHECK OUTS)","PROTECTIVE CLOTHING",
    "QUALITY ASSURANCE SUPPLIES","SHELF LABELS","STORE PROMOTIONAL SUPPLIES","UNIFORMS",
    "ELECTRICITY","PPAs","CAR FUEL","DIESEL FOR STANDBY GENERATORS","FUEL FOR RESALE",
    "SUSTAINABLE FUELS","TRUCK FUEL","HEATING","NATURAL GAS","COLLECTIVE SYSTEMS",
    "EXPIRED MEAT","GENERAL WASTE","GLASS WASTE","METAL WASTE","ORGANIC WASTE",
    "OTHER WASTE","PAPER & CARDBOARD WASTE","PLASTIC & FOIL WASTE",
    "RECYCLING EQUIPMENT BUY OR RENTAL","SANITARY WASTE","WASTE MANAGEMENT","WOOD WASTE","WATER",
]

MAX_QUERIES = 2

# ── Demo mode ─────────────────────────────────────────────────────────────────
# When True, the app serves pre-baked analyses from demo_data.json and makes NO API calls.
# Set to False once you are ready to take it live with the real API.
DEMO_MODE = True

import json as _json
import os as _os

def load_demo_data():
    path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "demo_data.json")
    try:
        with open(path) as f:
            return _json.load(f)
    except Exception:
        return {}

DEMO_DATA = load_demo_data()

def demo_key(cat, region, months):
    return f"{cat}|{region}|{months}"

def get_demo_summary(cat, region, months):
    return DEMO_DATA.get(demo_key(cat, region, months), {}).get("summary")

def get_demo_detail(cat, region, months, ch_name):
    rec = DEMO_DATA.get(demo_key(cat, region, months), {})
    return rec.get("details", {}).get(ch_name)

def demo_available_categories():
    cats = set()
    for k in DEMO_DATA.keys():
        parts = k.split("|")
        if len(parts) == 3:
            cats.add(parts[0])
    return cats
VALID_SCORES = [15, 45, 70, 98]
RISK_CFG = {
    15: ("LOW", "#22c55e", "#052e16", "#166534"),
    45: ("MODERATE", "#fbbf24", "#1c1400", "#92400e"),
    70: ("HIGH", "#fb923c", "#1c0a00", "#c2410c"),
    98: ("CRITICAL", "#f87171", "#1c0000", "#b91c1c"),
}
PIE_COLORS = ["#3b82f6", "#22c55e", "#fb923c", "#a855f7", "#ec4899", "#06b6d4", "#fbbf24", "#f87171"]

# ── Tool schemas ──────────────────────────────────────────────────────────────
TOOL_SUMMARY = {
    "name": "output_summary",
    "description": "Output lightweight cost-head summary with weighted average price forecast.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scope_note": {"type": "string", "description": "One-sentence note on data availability."},
            "weighted_avg_change_pct": {
                "type": "number",
                "description": "Estimated weighted average % change in total category cost over the forecast period. Negative = decrease."
            },
            "direction": {"type": "string", "enum": ["up", "down", "stable"]},
            "confidence_level": {"type": "string", "enum": ["High", "Medium", "Low"]},
            "last_updated_date": {"type": "string", "description": "DD Mon YYYY of most recent data source."},
            "primary_benchmarks": {"type": "string", "description": "Comma-separated list of main benchmarks used."},
            "key_assumptions": {"type": "string", "description": "2-3 short sentences on key assumptions."},
            "cost_heads": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "weight_pct": {"type": "number"},
                        "best_fit_index": {"type": "string"},
                        "is_proxy": {"type": "boolean"},
                        "projected_change_pct": {"type": "number", "description": "Projected % change in this cost head's input cost over the forecast period."},
                        "rationale": {"type": "string", "description": "Short rationale (1 sentence) explaining the inflation value, citing specific data."}
                    },
                    "required": ["name", "weight_pct", "best_fit_index", "is_proxy", "projected_change_pct", "rationale"]
                },
                "minItems": 4, "maxItems": 7
            }
        },
        "required": ["scope_note", "weighted_avg_change_pct", "direction", "confidence_level",
                     "last_updated_date", "primary_benchmarks", "key_assumptions", "cost_heads"]
    }
}

TOOL_DETAILED = {
    "name": "output_detailed_analysis",
    "description": "Detailed supply risk analysis for a single cost head.",
    "input_schema": {
        "type": "object",
        "properties": {
            "material_service": {"type": "string"},
            "current_supply_risk": {"type": "integer", "enum": [15, 45, 70, 98]},
            "forecasted_supply_risk": {"type": "integer", "enum": [15, 45, 70, 98]},
            "variables": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"heading": {"type": "string"}, "analysis": {"type": "string"}},
                    "required": ["heading", "analysis"]
                }, "minItems": 4, "maxItems": 6
            },
            "availability_forecast": {
                "type": "object",
                "properties": {
                    "outlook_period": {"type": "object",
                        "properties": {"heading": {"type": "string"}, "analysis": {"type": "string"}},
                        "required": ["heading", "analysis"]},
                    "best_case": {"type": "object",
                        "properties": {"heading": {"type": "string"}, "analysis": {"type": "string"}},
                        "required": ["heading", "analysis"]},
                    "base_case": {"type": "object",
                        "properties": {"heading": {"type": "string"}, "analysis": {"type": "string"}},
                        "required": ["heading", "analysis"]},
                    "worst_case": {"type": "object",
                        "properties": {"heading": {"type": "string"}, "analysis": {"type": "string"}},
                        "required": ["heading", "analysis"]}
                },
                "required": ["outlook_period", "best_case", "base_case", "worst_case"]
            },
            "additional_comments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "heading": {"type": "string"},
                        "analysis": {"type": "string"},
                        "references": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["heading", "analysis", "references"]
                }, "minItems": 3, "maxItems": 4
            },
            "all_references": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["material_service", "current_supply_risk", "forecasted_supply_risk",
                     "variables", "availability_forecast", "additional_comments", "all_references"]
    }
}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap');
:root {
    --bg: #0d1117; --bg2: #161b22; --bg3: #1c2230;
    --border: rgba(255,255,255,0.07); --border2: rgba(255,255,255,0.13);
    --t1: #f0f6fc; --t2: #8b949e; --t3: #484f58;
    --blue: #58a6ff; --blue-bg: rgba(88,166,255,0.08); --blue-bd: rgba(88,166,255,0.25);
    --green: #3fb950; --amber: #d29922; --red: #f85149;
    --radius: 8px; --radius-lg: 12px;
    --mono: 'DM Mono', monospace; --sans: 'DM Sans', sans-serif;
}
html, body, [class*="css"] { font-family: var(--sans); background: var(--bg); color: var(--t1); }
.stApp { background: var(--bg); }
.block-container { padding: 0 !important; max-width: 100% !important; }
h1, h2, h3 { color: var(--t1); }
#MainMenu, footer, header { visibility: hidden; }

.topbar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 20px; background: var(--bg2);
    border-bottom: 0.5px solid var(--border2);
}
.brand { font-size: 0.95rem; font-weight: 600; color: var(--t1); }
.brand-sub { font-size: 0.58rem; color: var(--t3); letter-spacing: 0.1em; text-transform: uppercase; }
.date-chip {
    font-size: 0.65rem; color: var(--t3); font-family: var(--mono);
    background: var(--blue-bg); border: 0.5px solid var(--blue-bd);
    border-radius: 5px; padding: 3px 9px; letter-spacing: 0.06em;
}

[data-testid="stColumns"] { gap: 0 !important; }
[data-testid="column"]:nth-child(1) { border-right: 0.5px solid var(--border2); }
[data-testid="column"]:nth-child(2) { border-right: 0.5px solid var(--border2); }

.lbl {
    font-size: 0.58rem; font-weight: 500; color: var(--t3);
    letter-spacing: 0.1em; text-transform: uppercase;
    font-family: var(--mono); margin-bottom: 6px; display: block;
}
.card {
    background: var(--bg2); border: 0.5px solid var(--border);
    border-radius: var(--radius-lg); padding: 16px; margin-bottom: 10px;
}
.card-sm { padding: 10px 12px; }
.card-amber { border-color: rgba(210,153,34,0.3) !important; }

/* Weighted Avg card (right column) */
.wac-title { font-size: 0.85rem; color: var(--t2); margin-bottom: 14px; line-height: 1.5; }
.wac-figure { font-size: 3rem; font-weight: 500; line-height: 1; margin-bottom: 6px; font-family: var(--sans); }
.wac-period { font-size: 0.8rem; color: var(--t2); margin-bottom: 16px; }
.wac-trend-card {
    background: rgba(63,185,80,0.06); border: 0.5px solid rgba(63,185,80,0.3);
    border-radius: var(--radius); padding: 10px 14px;
    font-size: 0.8rem; color: var(--t1); line-height: 1.8;
}
.wac-trend-card.dn { background: rgba(248,81,73,0.06); border-color: rgba(248,81,73,0.3); }
.wac-trend-card.up { background: rgba(251,146,60,0.06); border-color: rgba(251,146,60,0.3); }

/* Risk badges */
.rb {
    display: inline-block; border-radius: 5px;
    padding: 3px 10px; font-weight: 500; font-size: 0.75rem;
    letter-spacing: 0.05em; font-family: var(--mono);
}

/* Bullets */
.bul {
    border-left: 2px solid var(--border2); padding: 9px 12px;
    margin-bottom: 9px; border-radius: 0 6px 6px 0;
    background: rgba(255,255,255,0.02);
}
.bul-h { font-size: 0.82rem; font-weight: 500; color: var(--blue); }
.bul-b { font-size: 0.8rem; color: var(--t2); line-height: 1.65; margin-top: 3px; }

/* Scenarios */
.sc-best { border-left: 2px solid var(--green); padding: 9px 12px; background: rgba(63,185,80,0.04); border-radius: 0 7px 7px 0; margin-bottom: 7px; }
.sc-base { border-left: 2px solid var(--amber); padding: 9px 12px; background: rgba(210,153,34,0.04); border-radius: 0 7px 7px 0; margin-bottom: 7px; }
.sc-worst { border-left: 2px solid var(--red); padding: 9px 12px; background: rgba(248,81,73,0.04); border-radius: 0 7px 7px 0; margin-bottom: 7px; }
.sc-lbl { font-size: 0.6rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; font-family: var(--mono); margin-bottom: 2px; }
.sc-h { font-size: 0.82rem; font-weight: 500; color: var(--t1); }
.sc-b { font-size: 0.78rem; color: var(--t2); line-height: 1.6; margin-top: 3px; }

.ref { font-size: 0.65rem; color: var(--blue); word-break: break-all; line-height: 1.9; font-family: var(--mono); display: block; }

/* Streamlit widget overrides */
div[data-testid="stButton"] > button {
    background: var(--bg2) !important; border: 0.5px solid var(--border2) !important;
    border-radius: var(--radius) !important; color: var(--t1) !important;
    font-family: var(--sans) !important; font-size: 0.85rem !important;
    font-weight: 500 !important; padding: 0.5rem 1rem !important;
    width: 100% !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: var(--blue) !important; color: var(--blue) !important;
}
.stSelectbox label, .stRadio label { display: none; }
[data-testid="stSelectbox"] > div > div {
    background: var(--bg2) !important; border: 0.5px solid var(--border2) !important;
    border-radius: var(--radius) !important; color: var(--t1) !important;
    font-size: 0.82rem !important;
}
[data-testid="stRadio"] > div {
    background: var(--bg2); border: 0.5px solid var(--border2);
    border-radius: var(--radius); padding: 6px 10px;
}
[data-testid="stRadio"] label p { color: var(--t1) !important; font-size: 0.82rem !important; }
.stSelectbox svg { color: var(--t2) !important; }
.stExpander { background: var(--bg2); border: 0.5px solid var(--border); border-radius: var(--radius); }
.stExpander summary { font-size: 0.78rem; color: var(--t2); }

/* Placeholder */
.placeholder {
    background: var(--bg2); border: 1px dashed var(--border2);
    border-radius: var(--radius-lg); padding: 40px 24px;
    text-align: center; margin: 20px 0;
}
.placeholder-icon { font-size: 2rem; color: var(--t3); margin-bottom: 10px; }
.placeholder-text { font-size: 0.9rem; color: var(--t2); line-height: 1.7; }

hr.cp { border: none; border-top: 0.5px solid var(--border2); margin: 16px 0; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def today_str():
    return datetime.today().strftime("%d %B %Y")

def get_api_key():
    if DEMO_MODE:
        return None
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        st.error("API key not configured. Streamlit Cloud > Settings > Secrets > add ANTHROPIC_API_KEY.")
        st.stop()

def snap_risk(v):
    try: v = int(float(v))
    except: return 45
    return min(VALID_SCORES, key=lambda x: abs(x - v))

def risk_badge(score):
    score = snap_risk(score)
    label, fg, bg, bd = RISK_CFG[score]
    return f'<span class="rb" style="color:{fg};background:{bg};border:1px solid {bd};">&#9679; {score} \u2014 {label}</span>'

def extract_all_text(response):
    return "\n\n".join(b.text.strip() for b in response.content if hasattr(b, "type") and b.type == "text")

def extract_tool(response, name):
    for b in response.content:
        if hasattr(b, "type") and b.type == "tool_use" and b.name == name:
            return b.input
    raise ValueError(f"Tool '{name}' not called.")

def research(client, prompt):
    r = client.messages.create(
        model="claude-opus-4-5", max_tokens=2500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    return extract_all_text(r)

def structure(client, notes, tool, context):
    name = tool["name"]
    r = client.messages.create(
        model="claude-opus-4-5", max_tokens=2000,
        tools=[tool],
        tool_choice={"type": "tool", "name": name},
        messages=[{"role": "user", "content":
            f"Research notes:\n\n{notes}\n\n{context}\n\nCall {name} now."}],
    )
    return extract_tool(r, name)

# ── Module runners ────────────────────────────────────────────────────────────
def run_summary(cat, region, months, api_key):
    """One lightweight call: cost head structure + weighted avg forecast."""
    if DEMO_MODE:
        d = get_demo_summary(cat, region, months)
        if d is None:
            raise ValueError(
                f"Demo data not available for this combination ({cat} / {region} / {months}m). "
                f"Try one of the pre-loaded demo examples shown in the left panel."
            )
        return d
    c = anthropic.Anthropic(api_key=api_key)
    t = today_str()
    notes = research(c,
        f"Today is {t}. Research: {cat} in {region}. Forecast horizon: {months} months. "
        f"Identify 4-7 cost heads summing to 100% with best benchmark indices. "
        f"For each cost head, estimate the projected % change in its input cost over the next {months} months. "
        f"Use latest futures curves, forward prices, and analyst forecasts. "
        f"Provide a short rationale (1 sentence) for each inflation value, citing specific data points. "
        f"Then calculate the WEIGHTED AVERAGE % change in total category cost. "
        f"Note confidence level and last data date.")
    return structure(c, notes, TOOL_SUMMARY,
        f"Structure summary for {cat} in {region} over {months} months. "
        f"check_date = '{t}'. Weights must sum to 100. "
        f"For each cost head fill projected_change_pct (positive=increase) and rationale. "
        f"weighted_avg_change_pct must equal: sum of (projected_change_pct * weight_pct / 100) across all cost heads. "
        f"direction = up if weighted_avg_change_pct > 0, down if < 0, stable if approximately zero.")

def run_detailed(cat, region, months, cost_head, benchmark, api_key):
    """On-demand call for ONE cost head."""
    if DEMO_MODE:
        d = get_demo_detail(cat, region, months, cost_head)
        if d is None:
            raise ValueError(
                f"Demo detail not available for '{cost_head}'. "
                f"In this demo, click the highlighted cost head on the pie chart."
            )
        return d
    c = anthropic.Anthropic(api_key=api_key)
    t = today_str()
    notes = research(c,
        f"Today is {t}. DETAILED supply risk analysis for the cost head: '{cost_head}' "
        f"(benchmark: {benchmark}) within {cat} in {region}. Forecast horizon: {months} months. "
        f"Find latest data on: production issues, trade flows, import dependence, logistics, "
        f"geopolitical exposure, sanctions, energy input, weather, policy changes. "
        f"Provide outlook for next {months} months and 12-month best/base/worst scenarios. "
        f"Identify 3-4 buyer watchpoints. Include real source URLs.")
    return structure(c, notes, TOOL_DETAILED,
        f"Structure detailed analysis for {cost_head} ({benchmark}) within {cat} in {region}. "
        f"Outlook period: {months} months. "
        f"Risk scores ONLY: 15, 45, 70, 98. "
        f"Each heading: 3-6 words, UPPER CASE. Analysis: 2-4 factual sentences with figures.")

# ── Pie chart ──────────────────────────────────────────────────────────────────
def build_pie(cost_heads):
    labels = [h["name"] for h in cost_heads]
    values = [h["weight_pct"] for h in cost_heads]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.45,
        marker=dict(colors=PIE_COLORS[:len(labels)], line=dict(color="#0d1117", width=2)),
        textinfo="label+percent", textfont=dict(size=12, color="#f0f6fc", family="DM Sans"),
        hovertemplate="<b>%{label}</b><br>Weight: %{value}%<extra></extra>",
        sort=False,
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#8b949e"),
        margin=dict(l=0, r=0, t=10, b=10), height=380,
        showlegend=False,
    )
    return fig

# ── HTML helpers ──────────────────────────────────────────────────────────────
def bullet(heading, analysis, color="#58a6ff"):
    return f'<div class="bul"><div class="bul-h" style="color:{color};">&gt; {heading}:</div><div class="bul-b">{analysis}</div></div>'

def scenario(cls, lbl_color, lbl, heading, analysis):
    return f'<div class="{cls}"><div class="sc-lbl" style="color:{lbl_color};">{lbl}</div><div class="sc-h">{heading}</div><div class="sc-b">{analysis}</div></div>'

# ── Session state ─────────────────────────────────────────────────────────────
defaults = {
    "qc": 0, "summary": None, "summary_key": None,
    "detail_cache": {}, "selected_ch": None,
    "trigger_analyse": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Top bar ───────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="topbar">'
    f'<div><span class="brand">&#11203; CommodityPulse</span>'
    f'<div class="brand-sub">Procurement Intelligence Platform</div></div>'
    f'<span class="date-chip">Analysis date: {datetime.today().strftime("%d %b %Y").upper()}</span>'
    f'</div>', unsafe_allow_html=True)

if DEMO_MODE:
    st.markdown(
        '<div style="background:linear-gradient(90deg,rgba(251,146,60,0.12),rgba(251,146,60,0.04));'
        'border-bottom:0.5px solid rgba(251,146,60,0.35);padding:8px 20px;'
        'font-size:0.78rem;color:#fb923c;font-family:DM Sans,sans-serif;text-align:center;">'
        '&#9888; <strong>DEMO MODE</strong> &middot; Showing pre-loaded sample analyses. No live data is being fetched. '
        'Available demo categories: <strong>HOME DELIVERY TRANSPORT OPERATIONS</strong> (Europe, 3M) and '
        '<strong>DOORS (BUILDING MATERIALS)</strong> (North America, 6M). '
        '<a href="tel:+919305435404" style="color:#fb923c;text-decoration:underline;">Contact Ankur</a> for full access.'
        '</div>',
        unsafe_allow_html=True)

# ── Three columns ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1.8, 3.4, 2.4])

# PANEL 1 — Filters
with col1:
    st.markdown("<div style='padding:16px;'>", unsafe_allow_html=True)
    st.markdown('<span class="lbl">1. L3 Category</span>', unsafe_allow_html=True)
    selected_cat = st.selectbox("cat", CATEGORIES, label_visibility="collapsed", key="cat_sel")

    st.markdown('<span class="lbl" style="margin-top:10px;display:block;">2. Region</span>', unsafe_allow_html=True)
    selected_region = st.selectbox("reg",
        ["Europe", "North America", "Asia Pacific", "Middle East & Africa", "Latin America"],
        label_visibility="collapsed", key="reg_sel")

    st.markdown('<span class="lbl" style="margin-top:10px;display:block;">3. Forecast Period</span>', unsafe_allow_html=True)
    period_str = st.selectbox("per",
        ["1 Month", "3 Months", "6 Months"],
        label_visibility="collapsed", key="per_sel", index=1)
    forecast_months = int(period_str.split()[0])

    ql = MAX_QUERIES - st.session_state["qc"]
    st.markdown(
        f'<span class="lbl" style="margin-top:14px;display:block;">'
        f'Trial queries remaining: <strong style="color:#f0f6fc;">{ql}/{MAX_QUERIES}</strong></span>',
        unsafe_allow_html=True)

    if st.button("Run Analysis", use_container_width=True, disabled=(ql <= 0)):
        st.session_state["trigger_analyse"] = True

    st.markdown(
        '<hr class="cp">'
        '<div style="font-size:0.7rem;color:var(--t3);line-height:1.7;">'
        '<strong style="color:var(--t2);">How it works:</strong><br>'
        '1. Set the three inputs above<br>'
        '2. Click Run Analysis<br>'
        '3. Click any pie slice for<br>&nbsp;&nbsp;&nbsp;detailed cost head analysis<br><br>'
        'Detailed analysis runs on demand only, conserving credits.'
        '</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Trigger analyse
if st.session_state["trigger_analyse"]:
    st.session_state["trigger_analyse"] = False
    new_key = (selected_cat, selected_region, forecast_months)
    if st.session_state["summary_key"] != new_key:
        st.session_state["qc"] += 1
        st.session_state["summary"] = None
        st.session_state["detail_cache"] = {}
        st.session_state["selected_ch"] = None
        with st.spinner(f"Generating summary for {selected_cat} over {forecast_months} months..."):
            try:
                st.session_state["summary"] = run_summary(
                    selected_cat, selected_region, forecast_months, get_api_key())
                st.session_state["summary_key"] = new_key
            except Exception as e:
                st.error(f"Summary error: {e}")
        st.rerun()

summary = st.session_state.get("summary")
summary_key = st.session_state.get("summary_key")
inputs_changed = summary_key and summary_key != (selected_cat, selected_region, forecast_months)

# PANEL 2 — Pie chart
with col2:
    st.markdown("<div style='padding:16px;'>", unsafe_allow_html=True)
    if summary and not inputs_changed:
        st.markdown('<span class="lbl">Cost Head Composition</span>'
                    f'<div style="font-size:0.85rem;color:var(--t1);margin-bottom:14px;">{selected_cat} &middot; {selected_region}</div>',
                    unsafe_allow_html=True)
        fig = build_pie(summary["cost_heads"])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="pie_chart")

        st.markdown(
            '<div style="font-size:0.72rem;color:var(--t2);margin:6px 0 8px;text-align:center;">'
            'Click a cost head below to load its detailed analysis</div>',
            unsafe_allow_html=True)

        # Cost head selection buttons - always reliable
        ch_cols = st.columns(min(len(summary["cost_heads"]), 3))
        for i, ch in enumerate(summary["cost_heads"]):
            with ch_cols[i % 3]:
                active = (st.session_state.get("selected_ch") and
                          st.session_state["selected_ch"]["name"] == ch["name"])
                label = f"▶ {ch['name'][:22]} ({ch['weight_pct']}%)" if active else f"{ch['name'][:22]} ({ch['weight_pct']}%)"
                if st.button(label, key=f"chbtn_{i}", use_container_width=True):
                    st.session_state["selected_ch"] = ch
                    st.rerun()

        with st.expander("View supporting data and assumptions"):
            f = summary
            conf_color = {"High": "#3fb950", "Medium": "#d29922", "Low": "#f85149"}.get(f.get("confidence_level", "Medium"), "#d29922")
            st.markdown(
                f'<div style="font-size:0.78rem;color:var(--t2);line-height:1.7;">'
                f'<strong style="color:var(--t1);">Scope:</strong> {f.get("scope_note","")}<br><br>'
                f'<strong style="color:var(--t1);">Primary benchmarks:</strong> {f.get("primary_benchmarks","")}<br>'
                f'<strong style="color:var(--t1);">Last updated:</strong> {f.get("last_updated_date","")}<br>'
                f'<strong style="color:var(--t1);">Confidence:</strong> <span style="color:{conf_color};font-weight:500;">{f.get("confidence_level","")}</span><br><br>'
                f'<strong style="color:var(--t1);">Key assumptions:</strong> {f.get("key_assumptions","")}<br><br>'
                f'<strong style="color:var(--t1);">Cost-head benchmarks:</strong>'
                f'</div>',
                unsafe_allow_html=True)
            for h in summary["cost_heads"]:
                proxy = ' <span style="color:#fbbf24;font-size:0.65rem;font-family:DM Mono;">[PROXY]</span>' if h.get("is_proxy") else ""
                st.markdown(
                    f'<div style="font-size:0.78rem;color:var(--t2);margin-top:8px;padding:8px 12px;background:var(--bg);border-radius:6px;">'
                    f'<strong style="color:var(--t1);">{h["name"]} ({h["weight_pct"]}%)</strong>{proxy}<br>'
                    f'<span style="color:var(--blue);font-size:0.72rem;">{h["best_fit_index"]}</span><br>'
                    f'{h.get("brief_note","")}</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="placeholder" style="margin-top:40px;">'
            '<div class="placeholder-icon">&#9684;</div>'
            '<div class="placeholder-text">Set your three inputs on the left<br>'
            'and click <strong style="color:var(--blue);">Run Analysis</strong><br>'
            'to see the cost head composition.</div></div>',
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# PANEL 3 — Weighted Avg card
with col3:
    st.markdown("<div style='padding:16px;'>", unsafe_allow_html=True)
    if summary and not inputs_changed:
        pct = float(summary.get("weighted_avg_change_pct", 0))
        direction = summary.get("direction", "stable")
        is_down = pct < 0 or direction == "down"
        is_up = pct > 0 or direction == "up"
        arrow = "&darr;" if is_down else ("&uarr;" if is_up else "&rarr;")
        color = "#3fb950" if is_down else ("#fb923c" if is_up else "#d29922")
        trend_word = "Decrease" if is_down else ("Increase" if is_up else "Stable")
        trend_cls = "dn" if is_down else ("up" if is_up else "")
        conf = summary.get("confidence_level", "Medium")
        conf_color = {"High": "#3fb950", "Medium": "#d29922", "Low": "#f85149"}.get(conf, "#d29922")

        st.markdown('<span class="lbl">Estimated Weighted Average</span>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="wac-title">Price {"Increase" if is_up else "Decrease" if is_down else "Movement"}</div>'
            f'<div class="wac-figure" style="color:{color};">{arrow} {pct:+.2f}%</div>'
            f'<div class="wac-period">for next <strong style="color:var(--t1);">{forecast_months} {"Month" if forecast_months == 1 else "Months"}</strong></div>'
            f'<div class="wac-trend-card {trend_cls}">'
            f'<div>Trend: <strong style="color:{color};">{trend_word}</strong></div>'
            f'<div>Confidence: <strong style="color:{conf_color};">{conf}</strong></div>'
            f'<div style="font-size:0.7rem;color:var(--t3);margin-top:4px;">Updated: {summary.get("last_updated_date","")}</div>'
            f'</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="placeholder" style="margin-top:40px;">'
            '<div class="placeholder-icon">&#8645;</div>'
            '<div class="placeholder-text">Weighted average price<br>movement will appear here.</div></div>',
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── MIDDLE SECTION — Weighted Average Calculation Table (full width) ───────────
if summary and not inputs_changed:
    st.markdown('<hr style="border:none;border-top:0.5px solid var(--border2);margin:0;">', unsafe_allow_html=True)
    st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)

    st.markdown(
        '<span class="lbl">Weighted Average Calculation</span>'
        f'<div style="font-size:0.85rem;color:var(--t2);margin-bottom:12px;">'
        f'How the {forecast_months}-month weighted average price change of '
        f'<strong style="color:var(--t1);">{summary.get("weighted_avg_change_pct", 0):+.2f}%</strong> '
        f'was calculated for <strong style="color:var(--t1);">{selected_cat}</strong> ({selected_region}).'
        '</div>',
        unsafe_allow_html=True)

    # Build the calculation table
    rows_html = ""
    total_check = 0.0
    for ch in summary["cost_heads"]:
        try:
            wt = float(ch.get("weight_pct", 0))
        except: wt = 0.0
        try:
            infl = float(ch.get("projected_change_pct", 0))
        except: infl = 0.0
        weighted = round(wt * infl / 100, 3)
        total_check += weighted

        infl_color = "#fb923c" if infl > 0 else ("#3fb950" if infl < 0 else "#d29922")
        wgt_color = "#fb923c" if weighted > 0 else ("#3fb950" if weighted < 0 else "#d29922")
        infl_sign = "+" if infl > 0 else ""
        wgt_sign = "+" if weighted > 0 else ""
        proxy = ' <span style="color:#fbbf24;font-size:0.6rem;">[PROXY]</span>' if ch.get("is_proxy") else ""

        rows_html += (
            f'<tr style="border-bottom:0.5px solid rgba(255,255,255,0.04);">'
            f'<td style="padding:10px 12px;font-size:0.82rem;color:var(--t1);font-weight:500;">'
            f'{ch["name"]}{proxy}<br>'
            f'<span style="font-size:0.7rem;color:var(--blue);font-family:DM Mono;font-weight:400;">{ch["best_fit_index"]}</span></td>'
            f'<td style="padding:10px 12px;text-align:center;font-family:DM Mono;font-size:0.85rem;color:var(--t2);">{wt:.1f}%</td>'
            f'<td style="padding:10px 12px;text-align:center;font-family:DM Mono;font-size:0.9rem;color:{infl_color};font-weight:500;">{infl_sign}{infl:.2f}%</td>'
            f'<td style="padding:10px 12px;text-align:center;font-family:DM Mono;font-size:0.9rem;color:{wgt_color};font-weight:500;">{wgt_sign}{weighted:+.3f}%</td>'
            f'<td style="padding:10px 12px;font-size:0.78rem;color:var(--t2);line-height:1.55;">{ch.get("rationale","")}</td>'
            f'</tr>'
        )

    # Total row - use the model's reported weighted average
    reported_total = float(summary.get("weighted_avg_change_pct", 0))
    total_color = "#fb923c" if reported_total > 0 else ("#3fb950" if reported_total < 0 else "#d29922")
    total_sign = "+" if reported_total > 0 else ""

    table_html = (
        '<div class="card" style="overflow-x:auto;padding:0;">'
        '<table style="width:100%;border-collapse:collapse;">'
        '<thead><tr style="background:var(--bg);border-bottom:1px solid var(--border2);">'
        '<th style="padding:10px 12px;text-align:left;font-size:0.62rem;color:var(--t3);font-family:DM Mono;font-weight:500;text-transform:uppercase;letter-spacing:0.08em;">Cost Head / Benchmark</th>'
        '<th style="padding:10px 12px;text-align:center;font-size:0.62rem;color:var(--t3);font-family:DM Mono;font-weight:500;text-transform:uppercase;letter-spacing:0.08em;">Weight</th>'
        '<th style="padding:10px 12px;text-align:center;font-size:0.62rem;color:var(--t3);font-family:DM Mono;font-weight:500;text-transform:uppercase;letter-spacing:0.08em;">Inflation</th>'
        '<th style="padding:10px 12px;text-align:center;font-size:0.62rem;color:var(--t3);font-family:DM Mono;font-weight:500;text-transform:uppercase;letter-spacing:0.08em;">Wt &times; Infl</th>'
        '<th style="padding:10px 12px;text-align:left;font-size:0.62rem;color:var(--t3);font-family:DM Mono;font-weight:500;text-transform:uppercase;letter-spacing:0.08em;">Rationale</th>'
        '</tr></thead><tbody>'
        f'{rows_html}'
        '<tr style="background:rgba(88,166,255,0.08);border-top:1.5px solid var(--blue-bd);">'
        '<td style="padding:14px 12px;font-size:0.9rem;color:var(--t1);font-weight:600;">WEIGHTED AVERAGE</td>'
        '<td style="padding:14px 12px;text-align:center;font-family:DM Mono;font-size:0.85rem;color:var(--t2);font-weight:600;">100.0%</td>'
        '<td style="padding:14px 12px;text-align:center;color:var(--t3);font-family:DM Mono;font-size:0.75rem;">&mdash;</td>'
        f'<td style="padding:14px 12px;text-align:center;font-family:DM Mono;font-size:1.05rem;color:{total_color};font-weight:600;">{total_sign}{reported_total:.2f}%</td>'
        f'<td style="padding:14px 12px;font-size:0.75rem;color:var(--t2);">'
        f'Estimated weighted average price change over {forecast_months} months</td>'
        '</tr>'
        '</tbody></table></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:0.7rem;color:var(--t3);margin-top:6px;">'
        f'&#9888; Inflation values are estimates based on public forward signals as of {today_str()}. '
        f'Each cost-head weighted contribution is calculated as (Weight % &times; Inflation %) &divide; 100.</div>',
        unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── BOTTOM SECTION — Detailed analysis (full width) ─────────────────────────────
st.markdown('<hr style="border:none;border-top:0.5px solid var(--border2);margin:0;">', unsafe_allow_html=True)
st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)

selected_ch = st.session_state.get("selected_ch")

if not summary or inputs_changed:
    pass
elif not selected_ch:
    st.markdown(
        '<div class="placeholder">'
        '<div class="placeholder-icon">&#128269;</div>'
        '<div class="placeholder-text">Select a cost head from the pie chart above<br>'
        'to view detailed supply risk analysis.</div></div>',
        unsafe_allow_html=True)
else:
    # Build cache key
    ch_name = selected_ch["name"]
    cache_key = (selected_cat, selected_region, forecast_months, ch_name)
    detail_cache = st.session_state["detail_cache"]

    if cache_key not in detail_cache:
        with st.spinner(f"Loading detailed analysis for {ch_name}..."):
            try:
                result = run_detailed(
                    selected_cat, selected_region, forecast_months,
                    ch_name, selected_ch["best_fit_index"], get_api_key())
                detail_cache[cache_key] = result
                st.session_state["detail_cache"] = detail_cache
            except Exception as e:
                st.error(f"Detailed analysis error: {e}")

    d = detail_cache.get(cache_key)
    if d:
        st.markdown(
            f'<span class="lbl">Detailed Supply Risk Analysis</span>'
            f'<div style="font-size:1.1rem;font-weight:500;color:var(--t1);margin-bottom:3px;">'
            f'{d.get("material_service", selected_ch["best_fit_index"])}</div>'
            f'<div style="font-size:0.75rem;color:var(--t3);margin-bottom:16px;">'
            f'{selected_cat} &#8594; {ch_name} ({selected_ch["weight_pct"]}%) &middot; '
            f'{selected_region} &middot; {forecast_months}-month outlook</div>',
            unsafe_allow_html=True)

        # Risk scores row
        rc1, rc2, _ = st.columns([1, 1, 2])
        with rc1:
            st.markdown(
                f'<div class="card card-sm"><span class="lbl">Current Supply Risk</span>'
                f'{risk_badge(d["current_supply_risk"])}</div>',
                unsafe_allow_html=True)
        with rc2:
            st.markdown(
                f'<div class="card card-sm"><span class="lbl">Forecasted Supply Risk</span>'
                f'{risk_badge(d["forecasted_supply_risk"])}</div>',
                unsafe_allow_html=True)

        # Two-column layout: Variables (left) + Availability Forecast (right)
        bc1, bc2 = st.columns(2)
        with bc1:
            st.markdown('<span class="lbl" style="margin-top:8px;display:block;">Variables Impacting Availability</span>',
                        unsafe_allow_html=True)
            html = '<div class="card">'
            for v in d.get("variables", []):
                html += bullet(v.get("heading", ""), v.get("analysis", ""))
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
        with bc2:
            af = d.get("availability_forecast", {})
            st.markdown('<span class="lbl" style="margin-top:8px;display:block;">Availability Forecast</span>',
                        unsafe_allow_html=True)
            html = '<div class="card">'
            html += f'<span class="lbl" style="color:var(--t3);">{forecast_months}-Month Outlook</span>'
            o = af.get("outlook_period", {})
            html += bullet(o.get("heading", f"NEXT {forecast_months} MONTHS"), o.get("analysis", ""))
            html += '<span class="lbl" style="color:var(--t3);margin-top:10px;display:block;">12-Month Scenarios</span>'
            bc = af.get("best_case", {})
            mc = af.get("base_case", {})
            wc = af.get("worst_case", {})
            html += scenario("sc-best", "#3fb950", "&#9650; BEST CASE", bc.get("heading", ""), bc.get("analysis", ""))
            html += scenario("sc-base", "#d29922", "&#9670; BASE CASE", mc.get("heading", ""), mc.get("analysis", ""))
            html += scenario("sc-worst", "#f85149", "&#9660; WORST CASE", wc.get("heading", ""), wc.get("analysis", ""))
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

        # Additional comments — full width
        comments = d.get("additional_comments", [])
        if comments:
            st.markdown('<span class="lbl">Additional Comments</span>', unsafe_allow_html=True)
            html = '<div class="card">'
            for cm in comments:
                html += bullet(cm.get("heading", ""), cm.get("analysis", ""), "#fbbf24")
                refs = cm.get("references", [])
                if refs:
                    html += "".join(f'<a href="{r}" target="_blank" class="ref">{r}</a>' for r in refs)
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

        all_refs = d.get("all_references", [])
        if all_refs:
            with st.expander("All references"):
                for r in all_refs:
                    st.markdown(f'<a href="{r}" target="_blank" class="ref">{r}</a>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<style>'
    '.cp-contact{color:#21262d;text-decoration:none;transition:color 0.2s;}'
    '.cp-contact:hover{color:#58a6ff;}'
    '</style>'
    '<div style="text-align:center;padding:14px 0;border-top:0.5px solid rgba(255,255,255,0.06);'
    'font-size:0.65rem;color:var(--t3);line-height:2.2;">'
    'CommodityPulse &nbsp;&middot;&nbsp; Procurement Intelligence Platform &nbsp;&middot;&nbsp;'
    ' Powered by Anthropic Claude with live web search<br>'
    '<span style="color:#21262d;">&#9670; Ideation &nbsp;/&nbsp; Made &nbsp;/&nbsp; Developed by '
    '<strong style="color:var(--t3);">Ankur Phillips</strong> &nbsp;&middot;&nbsp; '
    '<a href="tel:+919305435404" class="cp-contact">+91 9305 435 404</a></span></div>',
    unsafe_allow_html=True)
