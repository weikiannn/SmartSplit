from collections import defaultdict

CURRENCIES = [
    "USD","EUR","GBP","MYR","SGD","JPY",
    "CAD","AUD","INR","CNY","THB","IDR","PHP"
]


def calculate_balances(expenses, target="MYR"):

    balances = defaultdict(float)

    for exp in expenses:

        payer = exp["payer_name"]

        balances[payer] += float(exp["amount"])

        for person, share in exp["splits"].items():
            balances[person] -= float(share)

    return {k: round(v,2) for k,v in balances.items()}


def simplified_settlement(balances):

    debtors=[]
    creditors=[]

    for person, bal in balances.items():

        if bal < -0.01:
            debtors.append([person,-bal])

        elif bal > 0.01:
            creditors.append([person,bal])

    i=j=0
    result=[]

    while i < len(debtors) and j < len(creditors):

        pay=min(debtors[i][1],creditors[j][1])

        result.append({
            "from":debtors[i][0],
            "to":creditors[j][0],
            "amount":round(pay,2)
        })

        debtors[i][1]-=pay
        creditors[j][1]-=pay

        if debtors[i][1] < 0.01:
            i+=1

        if creditors[j][1] < 0.01:
            j+=1

    return result