import pandas as pd
import numpy_financial as npf
from datetime import date

def amortization_table(interest_rate,
                       years,
                       principal,
                       payment,
                       is_renting=False,
                       after_n_months=None,
                       landlord_expenses=None,):


    dates_across_table = pd.date_range(date.today(),
        periods = years * 12,
        freq='MS')

    dates_across_table.name = "Payment_Date"

    # Build up the Amortization schedule as a DataFrame
    df = pd.DataFrame(index=dates_across_table,columns=['Payment', 'Principal', 'Interest', 'Balance'],
        dtype='float')

    # Add index by period (start at 1 not 0)
    df.reset_index(inplace=True)
    df.index += 1
    df.index.name = "Period"

    df["Payment"] = payment
    df["Principal"] = npf.ppmt(interest_rate / 12, df.index, years*12, principal)
    df["Interest"] = npf.ipmt(interest_rate / 12, df.index, years*12, principal)

    # Add in the additional principal payments


    # Store the Cumulative Principal Payments and ensure it never gets larger than the original principal
    df["Total Principal Owned"] = (df["Principal"]).cumsum()
    df["Total Principal Owned"] = df["Total Principal Owned"].clip(lower=-principal)
    df["Total Interest Paid"] = abs((df["Interest"]).cumsum())

    # Calculate the current balance for each period
    df["Balance"] = principal + df["Total Principal Owned"]

    # Determine the last payment date
    try:
        last_payment = df.query("Balance <= 0")["Balance"].idxmax(axis=1, skipna=True)
    except ValueError:
        last_payment = df.last_valid_index()

    last_payment_date = "{:%m-%d-%Y}".format(df.loc[last_payment, "Payment_Date"])


    # Get the payment info into a DataFrame in column order
    payment_info = (df[["Payment", "Principal", "Interest"]]
                    .sum().to_frame().T)

    # Format the Date DataFrame
    payment_details = pd.DataFrame.from_dict(dict([('payoff_date', [last_payment_date]),
                                               ('Interest Rate', [interest_rate]),
                                               ('Number of years', [years])
                                              ]))
    # Add a column showing how much we pay each period.
    payment_details["Period_Payment"] = round(payment, 2)

    payment_summary = pd.concat([payment_details, payment_info], axis=1)

    for column in ['Payment',
                   'Principal',
                   'Interest',
                   'Balance',
                   'Total Principal Owned',
                   'Total Interest Paid']:
        df[column] = df[column].abs()

    #Get total amount paid to the bank
    df['Total Paid to Bank'] = df['Total Principal Owned'] + df['Total Interest Paid']

    #Add contingency if you're renting it out
    # after_N_months = 'default'

    if is_renting == True:
        # Add contingency if you're renting it out
        after_N_months_value = df.loc[after_n_months, 'Total Paid to Bank'] #$ paid until that point
        #df.loc[after_n_months:, 'Total Paid to Bank'] = after_N_months_value #Paying nothing once someone rents
        df['Total Paid by You Specifically'] = df['Total Paid to Bank']
        for i in range(after_n_months + 1, len(df)+1):
            df.loc[i, 'Total Paid by You Specifically'] = df.loc[i-1, 'Total Paid by You Specifically'] + landlord_expenses
    return round(df,2), round(payment_summary,2), is_renting