# app.py — SmartSpend classy prototype (paste entire file; overwrite previous)
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import plotly.express as px
import os, json, time, re, base64
from datetime import datetime
from math import isclose

# -------------------- CONFIG --------------------
st.set_page_config(page_title="SmartSpend", page_icon="💠", layout="wide")
DATA_FILE = "expenses.csv"
BUDGET_FILE = "budgets.json"

# Pastel color palette (classy, minimal)
PASTEL = {
    "bg": "#FBFBFD",
    "card": "#FFFFFF",
    "muted": "#A3B0C3",
    "accent": "#9AD3BC",   # mint
    "accent2": "#A3B8F9",  # pastel blue
    "accent3": "#F6C8C2",  # soft coral
    "text": "#2E3A59"
}

DEFAULT_CATEGORIES = ["Food", "Shopping", "Bills", "Transport", "Entertainment", "Other"]
CATEGORY_KEYWORDS = {
    "Food": ["restaurant","dine","cafe","burger","pizza","food","canteen","coffee","tea","snack","lunch","dinner","cafe"],
    "Shopping": ["mall","amazon","flipkart","shopping","shop","store","clothes","shoes","cart"],
    "Bills": ["bill","electricity","water","phone","dth","grocery","rent","internet","billpayment"],
    "Transport": ["uber","ola","taxi","bus","train","fuel","petrol","metro","cab","auto"],
    "Entertainment": ["movie","netflix","spotify","concert","game","cinema","hotstar"],
}
CATEGORY_ICONS = {"Food":"🍽️","Shopping":"🛍️","Bills":"🧾","Transport":"🚕","Entertainment":"🎬","Other":"🔖"}
CATEGORY_COLORS = {"Food":"#F6C8C2","Shopping":"#A3B8F9","Bills":"#FFD8A8","Transport":"#C6E7D2","Entertainment":"#F0D7FF","Other":"#E6EEF8"}

# -------------------- HELPERS --------------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # ensure columns exist
            for c in ["date","amount","note","merchant","category"]:
                if c not in df.columns:
                    df[c] = ""
            # keep date as string for flexible formats; convert only when needed
            return df
        except Exception:
            try:
                os.remove(DATA_FILE)
            except Exception:
                pass
    df = pd.DataFrame(columns=["date","amount","note","merchant","category"])
    df.to_csv(DATA_FILE, index=False)
    return df

def save_data(df):
    df2 = df.copy()
    # normalize various date formats to ISO-like with time
    # try to coerce each value individually (mixed formats possible)
    df2['date'] = pd.to_datetime(df2['date'], errors='coerce', infer_datetime_format=True)
    # if any were NaT (coerce failed for some), try to parse as string day-first
    mask_nat = df2['date'].isna()
    if mask_nat.any():
        try:
            df2.loc[mask_nat, 'date'] = pd.to_datetime(df2.loc[mask_nat, 'date'].astype(str), dayfirst=True, errors='coerce', infer_datetime_format=True)
        except Exception:
            pass
    # final formatting: store as YYYY-MM-DD HH:MM:SS
    df2['date'] = df2['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
    df2.to_csv(DATA_FILE, index=False)

def load_budgets():
    if os.path.exists(BUDGET_FILE):
        try:
            with open(BUDGET_FILE, "r") as f:
                j = json.load(f)
                # ensure all default categories present
                for c in DEFAULT_CATEGORIES:
                    if c not in j:
                        j[c] = 0
                return j
        except Exception:
            pass
    budgets = {c:0 for c in DEFAULT_CATEGORIES}
    with open(BUDGET_FILE, "w") as f:
        json.dump(budgets, f)
    return budgets

def save_budgets(budgets):
    with open(BUDGET_FILE, "w") as f:
        json.dump(budgets, f)

def auto_category(note, merchant):
    text = (str(note) + " " + str(merchant)).lower()
    for cat, keys in CATEGORY_KEYWORDS.items():
        for k in keys:
            if k in text:
                return cat
    return "Other"

def currency(x):
    try:
        return f"₹{float(x):.2f}"
    except Exception:
        return f"₹{x}"

def pretty_datetime(s):
    try:
        dt = pd.to_datetime(s, errors='coerce', infer_datetime_format=True)
        if pd.isna(dt):
            return s
        return dt.strftime("%b %d, %Y %H:%M")
    except Exception:
        return s

def is_valid_phone(num):
    return bool(re.fullmatch(r"[6-9]\d{9}", num.strip()))

def is_valid_upi(upi):
    # basic UPI id pattern like name@bank or name@upi
    return bool(re.fullmatch(r"[.\w-]{2,}@[a-zA-Z]{3,}", upi.strip()))

# -------------------- STORAGE --------------------
df = load_data()
budgets = load_budgets()

# -------------------- STYLES (simple inline) --------------------
def card_style():
    return f"""
    <style>
      .card {{
        background: {PASTEL['card']};
        border-radius:12px;
        padding:12px;
        box-shadow: 0 6px 18px rgba(46,58,89,0.06);
      }}
      .small-muted {{ color:{PASTEL['muted']}; font-size:13px; }}
      .accent-pill {{ background:{PASTEL['accent']}; color:#fff; padding:6px 10px; border-radius:999px; font-weight:600; }}
    </style>
    """
st.markdown(card_style(), unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("<div style='padding:6px 0px'><h2 style='margin:0;color:#2E3A59'>SmartSpend</h2><div class='small-muted'>Classy prototype • Pastel UI</div></div>", unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1542228262-8b5f5bbd3a4d?auto=format&fit=crop&w=600&q=60", use_container_width=True)
    nav = st.radio("", ["Home", "Pay (Simulated)", "Add Expense", "Budgets", "Offline Transfer", "About"], index=0)
    st.markdown("---")
    st.caption("Prototype stores data locally (expenses.csv). No bank integration.")
    st.write("")

# -------------------- HOME / DASHBOARD --------------------
if nav == "Home":
    # header
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown("<div style='font-size:22px;font-weight:700;color:#2E3A59'>Overview</div>", unsafe_allow_html=True)
        st.markdown("<div class='small-muted'>Quick snapshot of your spending and budgets</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align:right'><span class='accent-pill'>Pastel • Classy</span></div>", unsafe_allow_html=True)

    st.markdown("")

    # metrics row
    total_spent = df['amount'].astype(float).sum() if not df.empty else 0.0
    # monthly spent: parse date column safely
    def month_spent(df_local):
        if df_local.empty:
            return 0.0
        try:
            parsed = pd.to_datetime(df_local['date'], errors='coerce', infer_datetime_format=True)
            now = datetime.now()
            mask = (parsed.dt.year == now.year) & (parsed.dt.month == now.month)
            return df_local.loc[mask, 'amount'].astype(float).sum()
        except Exception:
            return 0.0
    this_month = month_spent(df)

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Total Spent", currency(total_spent))
    col_b.metric("This Month", currency(this_month))
    active_budgets = sum(v for v in budgets.values() if v>0)
    col_c.metric("Active Budgets", f"₹{int(active_budgets)}")
    # remaining = budgets - spent in those categories
    spent_by_cat = {}
    if not df.empty:
        spent_by_cat = df.groupby("category")["amount"].sum().to_dict()
    remaining_total = sum(max(0, budgets.get(c,0) - spent_by_cat.get(c,0)) for c in budgets.keys())
    col_d.metric("Remaining", currency(remaining_total))

    st.markdown("---")

    # two columns: left charts, right mini-cards
    left, right = st.columns([3,1.2])

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Spending by category")
        if df.empty:
            st.info("No transactions yet — add one from 'Add Expense' or 'Pay' screens.")
        else:
            summary = df.groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False)
            fig = px.pie(summary, names="category", values="amount", hole=0.4)
            fig.update_traces(textinfo="percent+label")
            fig.update_layout(margin=dict(l=0,r=0,t=30,b=0), legend=dict(orientation="h"))
            st.plotly_chart(fig, use_container_width=True)
            # bar
            fig2 = px.bar(summary, x="category", y="amount", title="Amount by Category", color="category")
            fig2.update_layout(showlegend=False, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig2, use_container_width=True, height=260)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Recent transactions")
        if df.empty:
            st.write("No transactions recorded.")
        else:
            recent = df.sort_values("date", ascending=False).head(10).reset_index(drop=True)
            for idx, row in recent.iterrows():
                cat = row.get("category","Other")
                icon = CATEGORY_ICONS.get(cat,"🔖")
                merchant = row.get("merchant","")
                note = row.get("note","")
                date_n = pretty_datetime(row.get("date",""))
                amt = currency(row.get("amount",0))
                st.markdown(f"<div style='display:flex;align-items:center;gap:10px;padding:6px 0'><div style='font-size:20px'>{icon}</div><div style='flex:1'><b style='color:{PASTEL['text']}'>{merchant or note or cat}</b><div class='small-muted'>{note or merchant or ''} • <span class='small-muted'>{date_n}</span></div></div><div style='font-weight:700'>{amt}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Quick Actions")
        if st.button("➕ Add Expense", use_container_width=True):
            st.experimental_set_query_params(page="Add Expense")
        if st.button("📞 Pay Contact (Sim)", use_container_width=True):
            st.experimental_set_query_params(page="Pay (Simulated)")
        if st.button("📷 Scan QR (Sim)", use_container_width=True):
            # show a simulated QR result quickly
            st.success("Scanned QR: merchant@upi (simulated)")
            st.info("You can use the 'Pay (Simulated)' screen to send a payment using this QR result.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card' style='margin-top:12px'>", unsafe_allow_html=True)
        st.markdown("### Budgets")
        for cat in budgets.keys():
            color = CATEGORY_COLORS.get(cat, "#DDD")
            b = float(budgets.get(cat,0))
            s = float(spent_by_cat.get(cat,0)) if spent_by_cat.get(cat,0) is not None else 0.0
            pct = int(min(100, (s/b*100)) ) if b>0 else 0
            st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;padding:6px 0'><div><b>{CATEGORY_ICONS.get(cat)} {cat}</b><div class='small-muted'>{currency(s)} spent</div></div><div style='text-align:right'><div style='font-weight:700'>₹{int(b)}</div><div class='small-muted'>{pct}%</div></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------- PAY (SIMULATED UPI / QR) --------------------
elif nav == "Pay (Simulated)":
    st.markdown("<div style='font-size:20px;font-weight:700;color:#2E3A59'>Pay (Simulated)</div>", unsafe_allow_html=True)
    st.markdown("<div class='small-muted'>Send a simulated payment by phone number, UPI ID, or QR scan (demo only).</div>", unsafe_allow_html=True)
    st.markdown("---")
    col1, col2 = st.columns([2,1])
    with col1:
        pay_mode = st.radio("Choose method", ["Phone number", "UPI ID", "Scan QR (upload image)"], index=0, horizontal=True)
        if pay_mode == "Phone number":
            phone = st.text_input("Enter recipient phone number", placeholder="e.g., 9876543210")
            recipient = phone.strip()
            valid = is_valid_phone(recipient)
        elif pay_mode == "UPI ID":
            upi = st.text_input("Enter UPI ID", placeholder="e.g., name@bank")
            recipient = upi.strip()
            valid = is_valid_upi(recipient)
        else:  # QR
            uploaded = st.file_uploader("Upload QR image (simulated scan)", type=["png","jpg","jpeg"])
            if uploaded:
                st.image(uploaded, width=200)
                # for demo, simulate extracted UPI id
                recipient = "merchant@upi"
                st.success(f"Scanned: {recipient} (simulated)")
                valid = True
            else:
                recipient = ""
                valid = False

        amount = st.number_input("Amount (₹)", min_value=1.0, format="%.2f")
        note = st.text_input("Note (optional)", value="Payment via SmartSpend")
        auto_cat = st.checkbox("Auto-categorize transaction", value=True)
        if st.button("Send Payment"):
            if not valid:
                st.error("Please enter a valid phone number / UPI ID / scan a QR image.")
            else:
                with st.spinner("Processing payment (simulated)..."):
                    for i in range(30):
                        time.sleep(0.02)
                # add to local transactions
                category = auto_category(note, recipient) if auto_cat else "Other"
                new = {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "amount": float(amount),
                       "note": note,
                       "merchant": recipient,
                       "category": category}
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
                save_data(df)
                st.success(f"Sent {currency(amount)} to {recipient} (simulated). Recorded in transactions.")
                st.balloons()

    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Tips for demo")
        st.write("- Use a phone number (10 digits) for fastest demo.")
        st.write("- Upload a QR image to simulate scanning.")
        st.write("- Transactions are saved locally in `expenses.csv`.")
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------- ADD EXPENSE --------------------
elif nav == "Add Expense":
    st.markdown("<div style='font-size:20px;font-weight:700;color:#2E3A59'>Add Expense</div>", unsafe_allow_html=True)
    st.markdown("<div class='small-muted'>Manually add a UPI or cash expense (simulated).</div>", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("add_form"):
        col1, col2, col3 = st.columns([1.2,1.2,1])
        with col1:
            date_in = st.date_input("Date", value=datetime.today())
            time_in = st.time_input("Time", value=datetime.now().time())
        with col2:
            amt = st.number_input("Amount (₹)", min_value=0.0, format="%.2f", step=1.0)
            merchant = st.text_input("Merchant (optional)", placeholder="Cafe / Amazon / Rent")
        with col3:
            note = st.text_input("Note (optional)", placeholder="Lunch, socks, bill")
            auto = st.checkbox("Auto-categorize (recommended)", value=True)
            custom_cat = None
            if not auto:
                custom_cat = st.selectbox("Choose category", DEFAULT_CATEGORIES + ["Other"])
        submitted = st.form_submit_button("Save expense")
        if submitted:
            dt = datetime.combine(date_in, time_in).strftime("%Y-%m-%d %H:%M:%S")
            category = auto_category(note, merchant) if auto else custom_cat
            new = {"date": dt, "amount": float(amt), "note": note, "merchant": merchant, "category": category}
            df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
            save_data(df)
            st.success(f"Saved {currency(amt)} as {category} {CATEGORY_ICONS.get(category,'')}")
            st.balloons()

# -------------------- BUDGETS --------------------

elif nav == "Budgets":
    if 'spent_by_cat' not in locals():
        if not df.empty:
            spent_by_cat = df.groupby("category")["amount"].sum().to_dict()
        else:
            spent_by_cat = {}
    st.markdown("<div style='font-size:20px;font-weight:700;color:#2E3A59'>Budgets</div>", unsafe_allow_html=True)
    st.markdown("<div class='small-muted'>Set monthly budgets by category to receive alerts when exceeded.</div>", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("budget_form"):
        new_budgets = {}
        cols = st.columns(3)
        i = 0
        for c in DEFAULT_CATEGORIES:
            with cols[i%3]:
                val = st.number_input(f"{CATEGORY_ICONS.get(c)} {c}", min_value=0.0, value=float(budgets.get(c,0)), step=100.0, format="%.2f")
                new_budgets[c] = float(val)
            i += 1
        save_btn = st.form_submit_button("Save budgets")
        if save_btn:
            save_budgets(new_budgets)
            budgets = load_budgets()
            st.success("Budgets saved.")
            st.balloons()
    st.markdown("---")
    # Show alerts
    st.markdown("### Alerts")
    alerts = []
    for c in DEFAULT_CATEGORIES:
        b = float(budgets.get(c,0))
        s = float(spent_by_cat.get(c,0)) if spent_by_cat.get(c,0) is not None else 0
        if b>0 and s > b and not isclose(s,b):
            alerts.append((c, s-b))
    if alerts:
        for a in alerts:
            st.error(f"{a[0]} exceeded by {currency(a[1])}")
    else:
        st.success("No budget exceeded.")

# -------------------- OFFLINE TRANSFER --------------------
elif nav == "Offline Transfer":
    st.markdown("<div style='font-size:20px;font-weight:700;color:#2E3A59'>Offline Peer-to-Peer (Simulated)</div>", unsafe_allow_html=True)
    st.markdown("<div class='small-muted'>Simulate nearby device discovery and local transfer recording. Real implementation requires device APIs & secure cryptography.</div>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("Search nearby devices"):
        with st.spinner("Searching devices..."):
            for i in range(40):
                time.sleep(0.02)
        st.success("Devices found: Rahul Phone, Sneha Watch, Teja Wallet")
    device = st.selectbox("Choose device to transfer to", ["Rahul Phone", "Sneha Watch", "Teja Wallet"])
    amt = st.number_input("Amount to transfer (₹)", min_value=1.0, value=50.0, format="%.2f")
    note_off = st.text_input("Note for receiver", value="Split dinner")
    if st.button("Send offline transfer"):
        with st.spinner("Establishing secure channel (simulated)..."):
            for i in range(30):
                time.sleep(0.02)
        sim = {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "amount": float(amt), "note": f"Offline->{note_off}", "merchant": device, "category": "Other"}
        df = pd.concat([df, pd.DataFrame([sim])], ignore_index=True)
        save_data(df)
        st.success(f"Simulated ₹{amt:.2f} sent to {device}. Recorded locally.")
        st.balloons()

# -------------------- ABOUT --------------------
elif nav == "About":
    st.markdown("<div style='font-size:20px;font-weight:700;color:#2E3A59'>About SmartSpend</div>", unsafe_allow_html=True)
    st.markdown("<div class='small-muted'>Classy prototype (pastel) • Demo only • No bank integration</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.write("- Auto-categorization (keyword-based, demo).")
    st.write("- Budgets per-category + alerts.")
    st.write("- Offline peer-to-peer recording (simulated).")
    st.write("- Pay via phone / UPI ID / QR (simulated).")
    st.write("")
    st.write("How to run:")
    st.code("pip install -r requirements.txt\nstreamlit run app.py")
    st.markdown("---")
    st.write("Files created locally:")
    st.write(f"- `{DATA_FILE}` — transactions (CSV)")
    st.write(f"- `{BUDGET_FILE}` — budgets (JSON)")
