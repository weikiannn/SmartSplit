import io
import pandas as pd

def generate_excel(expenses, balances, settlements):

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # Expense Sheet
        rows=[]

        for e in expenses:

            row={
                "Description":e["description"],
                "Paid By":e["payer_name"],
                "Amount":e["amount"],
                "Currency":e["currency"]
            }

            for person,share in e["splits"].items():
                row[person]=share

            rows.append(row)

        pd.DataFrame(rows).to_excel(
            writer,
            sheet_name="Expenses",
            index=False
        )

        # Balance Sheet
        balance_rows=[]

        for name,bal in balances.items():

            balance_rows.append({
                "Member":name,
                "Net Balance":bal
            })

        pd.DataFrame(balance_rows).to_excel(
            writer,
            sheet_name="Balances",
            index=False
        )

        # Settlement Sheet
        pd.DataFrame(settlements).to_excel(
            writer,
            sheet_name="Settlement",
            index=False
        )

    return output.getvalue()