import streamlit as st
from datetime import datetime

from utils.supabase import supabase
from utils.calculations import calculate_balances, simplified_settlement
from utils.excel import generate_excel

if "user" not in st.session_state:
    st.switch_page("app.py")

if "current_group" not in st.session_state:
    st.switch_page("pages/2_Groups.py")

user = st.session_state.user
group = st.session_state.current_group

st.set_page_config(page_title="Settlement", layout="wide")

st.title(f"🤝 {group['name']} Settlement")

# -------------------------------------------------------
# Load Members
# -------------------------------------------------------

member_data = supabase.table("group_members")\
    .select("user_id, profiles(nickname)")\
    .eq("group_id", group["id"])\
    .execute().data

members = {}

for m in member_data:
    members[m["user_id"]] = m["profiles"]["nickname"]

# -------------------------------------------------------
# Load Expenses
# -------------------------------------------------------

raw = supabase.table("expenses")\
    .select("*")\
    .eq("group_id", group["id"])\
    .eq("status", "active")\
    .execute().data

expenses=[]

for e in raw:

    expenses.append({
        **e,
        "payer_name":members[e["payer_id"]]
    })

# -------------------------------------------------------
# Calculate
# -------------------------------------------------------

balances = calculate_balances(expenses)

settlements = simplified_settlement(balances)

# -------------------------------------------------------
# Balance Summary
# -------------------------------------------------------

st.header("💰 Net Balances")

if len(expenses)==0:
    st.success("No outstanding expenses!")

for person,bal in balances.items():

    col1,col2=st.columns([3,1])

    with col1:
        st.write(person)

    with col2:

        if bal>0:
            st.success(f"+ {bal:.2f}")

        elif bal<0:
            st.error(f"- {abs(bal):.2f}")

        else:
            st.info("0.00")

# -------------------------------------------------------
# Suggested Payments
# -------------------------------------------------------

st.divider()

st.header("📋 Suggested Settlement")

if len(settlements)==0:

    st.success("Everyone is settled 🎉")

else:

    for s in settlements:

        st.info(
            f"**{s['from']}** pays **{s['to']}** : RM {s['amount']:.2f}"
        )

# -------------------------------------------------------
# Download Report
# -------------------------------------------------------

st.divider()

excel = generate_excel(
    expenses,
    balances,
    settlements
)

st.download_button(
    "📥 Download Excel Report",
    excel,
    file_name=f"{group['name']}_settlement.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

# -------------------------------------------------------
# Complete Settlement
# -------------------------------------------------------

st.divider()

is_admin = group["admin_id"] == user.id

st.header("✅ Complete Settlement")

if is_admin:

    st.warning(
        "Only the group admin can finalize the settlement."
    )

    if st.button(
        "DONE SETTLEMENT",
        use_container_width=True,
        type="primary"
    ):

        supabase.table("settlements").insert({

            "group_id":group["id"],

            "settled_by":user.id,

            "settled_at":datetime.utcnow().isoformat()

        }).execute()

        supabase.table("expenses")\
            .update({
                "status":"settled"
            })\
            .eq("group_id",group["id"])\
            .execute()

        st.success("Settlement completed!")

        st.balloons()

        st.rerun()

else:

    st.info("Waiting for the group admin to complete settlement.")

# -------------------------------------------------------
# Settlement History
# -------------------------------------------------------

st.divider()

st.header("📚 Settlement History")

history = supabase.table("settlements")\
    .select("*")\
    .eq("group_id",group["id"])\
    .order("settled_at",desc=True)\
    .execute().data

if len(history)==0:

    st.caption("No settlement history yet.")

else:

    for h in history:

        name = members.get(h["settled_by"],"Unknown")

        with st.container(border=True):

            st.write(f"**Completed by:** {name}")

            st.caption(h["settled_at"])

# -------------------------------------------------------
# Navigation
# -------------------------------------------------------

st.divider()

if st.button("← Back to Expenses", use_container_width=True):

    st.switch_page("pages/3_Expenses.py")