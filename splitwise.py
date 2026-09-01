import streamlit as st
import pandas as pd
import requests
from collections import defaultdict
import io

# List of supported currencies
CURRENCIES = ["USD", "EUR", "GBP", "MYR", "SGD", "JPY", "CAD", "AUD", "INR", "CNY", "THB", "IDR", "PHP", "AED", "CHF"]

@st.cache_data(ttl=3600)
def get_exchange_rates(base_currency="USD"):
    """Fetches live exchange rates relative to base_currency using free API."""
    url = f"https://open.er-api.com/v6/latest/{base_currency}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("result") == "success":
            return data.get("rates", {})
        else:
            return {c: 1.0 for c in CURRENCIES}
    except Exception:
        return {c: 1.0 for c in CURRENCIES}

def calculate_balances(expenses, target_currency, rates):
    """Calculates net balance for every member in target currency."""
    balances = defaultdict(float)
    for exp in expenses:
        payer = exp["payer"]
        orig_amount = exp["amount"]
        orig_currency = exp["currency"]
        splits = exp["splits"]

        rate_orig = rates.get(orig_currency, 1.0)
        rate_target = rates.get(target_currency, 1.0)
        fx_ratio = rate_target / rate_orig if rate_orig != 0 else 1.0

        balances[payer] += orig_amount * fx_ratio
        for person, owed in splits.items():
            balances[person] -= owed * fx_ratio
            
    return {k: round(v, 2) for k, v in balances.items()}

def get_simplified_settlements(balances):
    """Minimizes transaction count by clearing debts via net balances."""
    debtors, creditors = [], []
    for person, balance in balances.items():
        if balance < -0.009:
            debtors.append({'name': person, 'amount': -balance})
        elif balance > 0.009:
            creditors.append({'name': person, 'amount': balance})

    settlements = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        settlement_amount = round(min(debtor['amount'], creditor['amount']), 2)

        if settlement_amount > 0:
            settlements.append({
                'from': debtor['name'],
                'to': creditor['name'],
                'amount': settlement_amount
            })

        debtor['amount'] -= settlement_amount
        creditor['amount'] -= settlement_amount

        if round(debtor['amount'], 2) <= 0:
            i += 1
        if round(creditor['amount'], 2) <= 0:
            j += 1

    return settlements

def get_unsimplified_settlements(expenses, target_currency, rates):
    """Direct bilateral debts per expense without net debt cancellation."""
    direct_debts = defaultdict(lambda: defaultdict(float))
    
    for exp in expenses:
        payer = exp["payer"]
        orig_currency = exp["currency"]
        rate_orig = rates.get(orig_currency, 1.0)
        rate_target = rates.get(target_currency, 1.0)
        fx_ratio = rate_target / rate_orig if rate_orig != 0 else 1.0

        for person, owed in exp["splits"].items():
            if person != payer:
                direct_debts[person][payer] += owed * fx_ratio

    settlements = []
    for debtor, creditors in direct_debts.items():
        for creditor, amount in creditors.items():
            if round(amount, 2) > 0:
                settlements.append({
                    'from': debtor,
                    'to': creditor,
                    'amount': round(amount, 2)
                })
    return settlements

def generate_excel_report(expenses, members, balances, settlements, target_currency, rates, method):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        settlement_df = pd.DataFrame(settlements if settlements else [{"from": "N/A", "to": "N/A", "amount": 0.0}])
        settlement_df.rename(columns={
            "from": "Debtor (Who Pays)",
            "to": "Creditor (Who Receives)",
            "amount": f"Amount ({target_currency})"
        }, inplace=True)
        settlement_df.to_excel(writer, sheet_name=f"Summary ({method})", index=False, startrow=3)

        net_rows = []
        for m in members:
            total_paid_converted = 0.0
            total_share_converted = 0.0
            for exp in expenses:
                rate_orig = rates.get(exp["currency"], 1.0)
                rate_target = rates.get(target_currency, 1.0)
                fx_ratio = rate_target / rate_orig if rate_orig != 0 else 1.0

                if exp["payer"] == m:
                    total_paid_converted += exp["amount"] * fx_ratio
                if m in exp["splits"]:
                    total_share_converted += exp["splits"][m] * fx_ratio

            net_bal = balances.get(m, 0.0)
            status = "Gets Back" if net_bal > 0 else ("Owes" if net_bal < 0 else "Settled")
            net_rows.append({
                "Member": m,
                f"Total Paid ({target_currency})": round(total_paid_converted, 2),
                f"Total Share Owed ({target_currency})": round(total_share_converted, 2),
                f"Net Balance ({target_currency})": round(net_bal, 2),
                "Status": status
            })
        balance_df = pd.DataFrame(net_rows)
        balance_df.to_excel(writer, sheet_name=f"Summary ({method})", index=False, startrow=len(settlement_df) + 7)

        matrix_rows = []
        for idx, exp in enumerate(expenses, 1):
            rate_orig = rates.get(exp["currency"], 1.0)
            rate_target = rates.get(target_currency, 1.0)
            fx_ratio = rate_target / rate_orig if rate_orig != 0 else 1.0

            row = {
                "ID": idx,
                "Description": exp["description"],
                "Paid By": exp["payer"],
                "Original Amount": exp["amount"],
                "Currency": exp["currency"],
                f"Converted Total ({target_currency})": round(exp["amount"] * fx_ratio, 2),
                "Split Method": exp.get("split_type", "Equal")
            }
            for m in members:
                row[f"{m} Share ({target_currency})"] = round(exp["splits"].get(m, 0.0) * fx_ratio, 2)
            matrix_rows.append(row)

        breakdown_df = pd.DataFrame(matrix_rows)
        breakdown_df.to_excel(writer, sheet_name="Expense Breakdown", index=False)

    return output.getvalue()

# --- Streamlit UI ---
st.set_page_config(page_title="Multi-Currency Debt Simplifier", page_icon="💱", layout="wide")
st.title("💱 Multi-Currency Group Debt Simplifier")

live_rates = get_exchange_rates("USD")

if "members" not in st.session_state:
    st.session_state.members = ["Alice", "Bob", "Charlie"]
if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "editing_idx" not in st.session_state:
    st.session_state.editing_idx = None

# Sidebar Controls
st.sidebar.header("⚙️ Global Settings")
target_currency = st.sidebar.selectbox("🎯 Target Settlement Currency", CURRENCIES, index=CURRENCIES.index("USD"))
settlement_method = st.sidebar.radio(
    "🔄 Settlement Method",
    ["Simplified (Min. Transactions)", "Unsimplified (Direct Debts)"],
    help="Simplified minimizes payment steps. Unsimplified keeps direct item-by-item balances."
)

st.sidebar.divider()
st.sidebar.header("1. Manage Members")
with st.sidebar.form("add_member_form", clear_on_submit=True):
    new_member = st.text_input("Add new member:")
    if st.form_submit_button("Add Member") and new_member.strip():
        clean_name = new_member.strip()
        if clean_name not in st.session_state.members:
            st.session_state.members.append(clean_name)
            st.rerun()

if st.session_state.members:
    member_to_remove = st.sidebar.selectbox("Remove member:", st.session_state.members)
    if st.sidebar.button("Remove Selected Member"):
        st.session_state.members.remove(member_to_remove)
        st.session_state.expenses = [
            exp for exp in st.session_state.expenses 
            if exp["payer"] != member_to_remove and member_to_remove not in exp["splits"]
        ]
        st.session_state.editing_idx = None
        st.rerun()

st.sidebar.write("**Current Members:**", ", ".join(st.session_state.members))
st.sidebar.divider()
if st.sidebar.button("Reset Everything"):
    st.session_state.expenses = []
    st.session_state.members = ["Alice", "Bob", "Charlie"]
    st.session_state.editing_idx = None
    st.rerun()

col1, col2 = st.columns([1.3, 1])

with col1:
    is_editing = st.session_state.editing_idx is not None
    st.subheader("✏️ Edit Expense" if is_editing else "2. Add Expense")

    if len(st.session_state.members) < 2:
        st.warning("Please add at least 2 group members.")
    else:
        if is_editing:
            exp_to_edit = st.session_state.expenses[st.session_state.editing_idx]
            def_desc = exp_to_edit["description"]
            def_payer = exp_to_edit["payer"] if exp_to_edit["payer"] in st.session_state.members else st.session_state.members[0]
            def_amount = exp_to_edit["amount"]
            def_currency = exp_to_edit.get("currency", "USD")
            def_type = exp_to_edit.get("split_type", "Equal")
        else:
            def_desc = "Dinner"
            def_payer = st.session_state.members[0]
            def_amount = 120.0
            def_currency = "USD"
            def_type = "Equal"

        desc = st.text_input("Description", value=def_desc)
        p_col1, p_col2, p_col3 = st.columns([2, 2, 1.5])
        with p_col1:
            payer = st.selectbox("Who paid?", st.session_state.members, index=st.session_state.members.index(def_payer))
        with p_col2:
            amount = st.number_input("Amount", min_value=0.01, step=1.0, value=float(def_amount))
        with p_col3:
            currency = st.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(def_currency))

        split_type = st.radio("Split Method", ["Equal", "Exact Amounts", "Percentage (%)"], 
                             index=["Equal", "Exact Amounts", "Percentage (%)"].index(def_type), horizontal=True)

        st.write("### 👥 Select & Customize People Involved")
        
        splits = {}
        checked_members = []
        
        cb_cols = st.columns(min(len(st.session_state.members), 4))
        for idx, m in enumerate(st.session_state.members):
            with cb_cols[idx % 4]:
                is_checked_def = True
                if is_editing and m not in exp_to_edit["splits"]:
                    is_checked_def = False
                checked = st.checkbox(m, value=is_checked_def, key=f"cb_{m}")
                if checked:
                    checked_members.append(m)

        valid_input = True

        if not checked_members:
            st.error("Please tick at least one person to split this expense.")
            valid_input = False
        else:
            if split_type == "Equal":
                per_person = amount / len(checked_members)
                splits = {m: per_person for m in checked_members}
                st.info(f"💡 {currency} {amount:.2f} split equally among {len(checked_members)} people = **{currency} {per_person:.2f} each**")

            elif split_type == "Exact Amounts":
                total_entered = 0.0
                st.write(f"**Enter exact amounts in {currency} for ticked members:**")
                
                auto_share = round(amount / len(checked_members), 2)
                for m in checked_members:
                    default_val = auto_share
                    if is_editing and m in exp_to_edit["splits"]:
                        default_val = float(exp_to_edit["splits"][m])

                    val = st.number_input(f"{m}'s share ({currency})", min_value=0.0, value=float(default_val), step=1.0, key=f"exact_{m}")
                    splits[m] = val
                    total_entered += val

                diff = round(amount - total_entered, 2)
                if abs(diff) > 0.01:
                    if diff > 0:
                        st.warning(f"⚠️ Custom inputs sum to **{currency} {total_entered:.2f}**. Remaining **{currency} {diff:.2f}** auto-balanced.")
                    else:
                        st.warning(f"⚠️ Custom inputs sum to **{currency} {total_entered:.2f}** (exceeds total). Shares scaled down.")
                    
                    if total_entered > 0:
                        splits = {m: (val / total_entered) * amount for m, val in splits.items()}
                    else:
                        splits = {m: amount / len(checked_members) for m in checked_members}

            elif split_type == "Percentage (%)":
                total_pct = 0.0
                st.write("**Enter percentages for ticked members:**")

                auto_pct = round(100.0 / len(checked_members), 2)
                for m in checked_members:
                    default_pct = auto_pct
                    if is_editing and m in exp_to_edit["splits"]:
                        default_pct = float((exp_to_edit["splits"][m] / exp_to_edit["amount"]) * 100.0)

                    pct = st.number_input(f"{m}'s share (%)", min_value=0.0, max_value=100.0, value=float(default_pct), step=1.0, key=f"pct_{m}")
                    splits[m] = (pct / 100.0) * amount
                    total_pct += pct

                diff_pct = round(100.0 - total_pct, 2)
                if abs(diff_pct) > 0.01:
                    st.warning(f"⚠️ Percentages total **{total_pct:.1f}%**. Auto-normalizing shares to 100%.")
                    if total_pct > 0:
                        splits = {m: (val / (total_pct / 100.0)) for m, val in splits.items()}

        b_col1, b_col2 = st.columns([1, 1])
        with b_col1:
            btn_title = "Update Expense" if is_editing else "Add Expense"
            if st.button(btn_title, type="primary") and valid_input:
                new_exp = {
                    "description": desc,
                    "payer": payer,
                    "amount": amount,
                    "currency": currency,
                    "split_type": split_type,
                    "splits": splits
                }
                if is_editing:
                    st.session_state.expenses[st.session_state.editing_idx] = new_exp
                    st.session_state.editing_idx = None
                else:
                    st.session_state.expenses.append(new_exp)
                st.rerun()

        with b_col2:
            if is_editing and st.button("Cancel"):
                st.session_state.editing_idx = None
                st.rerun()

    if st.session_state.expenses:
        st.subheader("📜 Expense Log")
        for i, exp in enumerate(st.session_state.expenses):
            l_col1, l_col2, l_col3 = st.columns([3, 1, 1])
            with l_col1:
                st.write(f"• **{exp['payer']}** paid **{exp['currency']} {exp['amount']:.2f}** for *{exp['description']}*")
            with l_col2:
                if st.button("✏️ Edit", key=f"edit_b_{i}"):
                    st.session_state.editing_idx = i
                    st.rerun()
            with l_col3:
                if st.button("🗑️ Delete", key=f"del_b_{i}"):
                    st.session_state.expenses.pop(i)
                    if st.session_state.editing_idx == i:
                        st.session_state.editing_idx = None
                    st.rerun()

with col2:
    st.subheader(f"3. Settlements ({target_currency})")
    if st.session_state.expenses:
        balances = calculate_balances(st.session_state.expenses, target_currency, live_rates)

        if "Simplified" in settlement_method:
            settlements = get_simplified_settlements(balances)
            mode_label = "Simplified (Min. Transactions)"
        else:
            settlements = get_unsimplified_settlements(st.session_state.expenses, target_currency, live_rates)
            mode_label = "Unsimplified (Direct Debts)"

        st.write("#### Net Balances")
        for person, bal in balances.items():
            if bal > 0:
                st.write(f"🟢 **{person}** gets back **{target_currency} {bal:.2f}**")
            elif bal < 0:
                st.write(f"🔴 **{person}** owes **{target_currency} {abs(bal):.2f}**")
            else:
                st.write(f"⚪ **{person}** is settled up")

        st.divider()

        st.write(f"#### Payments ({mode_label})")
        if not settlements:
            st.success("Everyone is settled up!")
        else:
            for s in settlements:
                st.info(f"👉 **{s['from']}** pays **{s['to']}** → **{target_currency} {s['amount']:.2f}**")

        st.divider()

        excel_bytes = generate_excel_report(
            st.session_state.expenses, st.session_state.members, balances, settlements, target_currency, live_rates, mode_label
        )
        st.download_button(
            label=f"📊 Download Excel Report ({target_currency})",
            data=excel_bytes,
            file_name=f"group_expenses_{target_currency}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )