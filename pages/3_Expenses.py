import streamlit as st
from utils.supabase import supabase
from utils.calculations import *

if "user" not in st.session_state:
    st.switch_page("app.py")

if "current_group" not in st.session_state:
    st.switch_page("pages/2_Groups.py")

user = st.session_state.user
group = st.session_state.current_group

st.set_page_config(page_title="Expenses", layout="wide")

st.title(f"💸 {group['name']}")

# -----------------------------------------------------
# Load Members
# -----------------------------------------------------

members_raw = supabase.table("group_members")\
    .select("user_id, profiles(nickname)")\
    .eq("group_id", group["id"])\
    .execute().data

members=[]
member_names=[]

for m in members_raw:

    members.append({
        "id":m["user_id"],
        "name":m["profiles"]["nickname"]
    })

    member_names.append(m["profiles"]["nickname"])

# -----------------------------------------------------
# Load Expenses
# -----------------------------------------------------

raw = supabase.table("expenses")\
    .select("*")\
    .eq("group_id", group["id"])\
    .eq("status","active")\
    .execute().data

expenses=[]

for e in raw:

    payer_name=""

    for m in members:
        if m["id"]==e["payer_id"]:
            payer_name=m["name"]

    expenses.append({
        **e,
        "payer_name":payer_name
    })

is_admin = group["admin_id"]==user.id

# -----------------------------------------------------
# ADD EXPENSE
# -----------------------------------------------------

st.header("➕ Add Expense")

with st.form("expense"):

    desc = st.text_input("Description")

    col1,col2,col3=st.columns(3)

    with col1:

        payer = st.selectbox(
            "Paid By",
            member_names
        )

    with col2:

        amount = st.number_input(
            "Amount",
            min_value=0.01,
            value=10.0
        )

    with col3:

        currency = st.selectbox(
            "Currency",
            CURRENCIES,
            index=3
        )

    split_method = st.radio(
        "Split Method",
        ["Equal","Exact","Percentage"],
        horizontal=True
    )

    selected=[]

    st.write("### Members")

    cols=st.columns(min(4,len(member_names)))

    for i,name in enumerate(member_names):

        with cols[i%4]:

            if st.checkbox(name,True,key=f"m_{i}"):

                selected.append(name)

    splits={}

    if split_method=="Equal":

        share=round(amount/len(selected),2)

        for s in selected:
            splits[s]=share

        st.info(f"{share} each")

    elif split_method=="Exact":

        for s in selected:

            splits[s]=st.number_input(
                s,
                value=float(amount/len(selected)),
                key=s
            )

    else:

        total=0

        temp={}

        for s in selected:

            p=st.number_input(
                f"{s} %",
                value=float(100/len(selected)),
                key=f"p{s}"
            )

            temp[s]=p
            total+=p

        for k,v in temp.items():

            splits[k]=round(amount*v/total,2)

    submit=st.form_submit_button("Add Expense")

if submit:

    payer_id=""

    for m in members:
        if m["name"]==payer:
            payer_id=m["id"]

    supabase.table("expenses").insert({

        "group_id":group["id"],

        "payer_id":payer_id,

        "created_by":user.id,

        "description":desc,

        "amount":amount,

        "currency":currency,

        "split_type":split_method,

        "splits":splits

    }).execute()

    st.success("Expense Added")

    st.rerun()

# -----------------------------------------------------
# EXPENSE LOG
# -----------------------------------------------------

st.divider()

st.header("📜 Expense Log")

if len(expenses)==0:

    st.info("No expenses yet.")

else:

    for exp in expenses:

        can_edit=(exp["created_by"]==user.id) or is_admin

        with st.container(border=True):

            col1,col2=st.columns([5,1])

            with col1:

                st.write(
                    f"### {exp['description']}"
                )

                st.write(
                    f"**{exp['payer_name']}** paid **{exp['currency']} {exp['amount']}**"
                )

                for person,share in exp["splits"].items():

                    st.write(f"- {person}: {share}")

            with col2:

                if can_edit:

                    if st.button("🗑",key=exp["id"]):

                        supabase.table("expenses")\
                            .delete()\
                            .eq("id",exp["id"])\
                            .execute()

                        st.rerun()

# -----------------------------------------------------
# BALANCES
# -----------------------------------------------------

st.divider()

st.header("💰 Current Balances")

balances=calculate_balances(expenses)

for person,bal in balances.items():

    if bal>0:

        st.success(f"{person} gets back RM {bal}")

    elif bal<0:

        st.error(f"{person} owes RM {abs(bal)}")

    else:

        st.info(f"{person} settled")

# -----------------------------------------------------
# SETTLEMENT PREVIEW
# -----------------------------------------------------

st.divider()

st.header("🤝 Suggested Payments")

settle=simplified_settlement(balances)

if len(settle)==0:

    st.success("Everyone is settled!")

else:

    for s in settle:

        st.write(
            f"**{s['from']}** ➜ **{s['to']}** : RM {s['amount']}"
        )

st.divider()

if st.button("Go To Settlement Page"):

    st.switch_page("pages/4_Settlement.py")