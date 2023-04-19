import streamlit as st
import pandas as pd
from helium import *
from amortization_table import amortization_table #see custom file in folder
from update_current_mortgage_rate import update_mortgage_rates #see custom file in folder

import numpy_financial as npf
import plotly.express as px

st.set_page_config(page_title="Amortization",
    page_icon='🏡',
    layout="centered",
    initial_sidebar_state="auto")

st.title("Amortization Analysis")
st.subheader("Lets start by defining the loan parameters:")

# Load in the most recent mortgage rates from Freddie Mac
rates = pd.read_parquet('mortgage_rates_FM.parquet')

# Check if it has been more than a week since the last update
last_update = pd.to_datetime(rates['date'].max())
one_week_ago = pd.to_datetime(dt.date.today() - dt.timedelta(days=7))

# Call function if the rates are outdated and the user wants to
if last_update <= one_week_ago:
    # Create a button to update mortgage rates
    if st.button("Update Mortgage Rates from Freddie Mac? The last pulled rates may be outdated"):
        update_mortgage_rates()
        st.success("Mortgage rates updated successfully!")

currentRate30, currentRate15 = rates['30yr'].iloc[-1], rates['15yr'].iloc[-1]

col1, col2, col3 = st.columns(3)
with col1:
   loan_amount = st.number_input("What is the Loan Amount?", value=500000,
    step=500)   # The loan amount in dollars

with col2:
   years = st.number_input('How many years is the mortgage?', min_value = 0, max_value = 60, value = 30, step = 15)
   term = years * 12             # The loan term in months

default_rate = currentRate15 if years == 15 else currentRate30
with col3:
    yearly_interest_rate = st.number_input("What's the Annual Interest Rate?",
       min_value = 0.1,
       max_value = 10.5,
       value = default_rate,
       step=0.01,) / 100
    
monthly_interest_rate = yearly_interest_rate / 12 # The monthly interest rate

payment = npf.pmt(rate=monthly_interest_rate,
                  nper=term,
                  pv=loan_amount,
                  fv=0,
                  when='end').round(2) # The monthly payment in dollars

st.subheader(f"The monthly payment would be approximately ${abs(payment)}")
st.info("""It is important to consider other costs that go into owning a home such as
         insurances, repairs, renovations, furninshings and other unexpected costs.
         This calculator is for educational purposes only. As with any large investment decision,
         it is important to consider speaking with a financial professional.""")

extraPmt1, extraPmt2, extraPmt3 = st.columns(3)
with extraPmt1:
   taxes = st.number_input("Estimated annual taxes:", value=6000,
    step=200, min_value = 0, max_value = loan_amount)
with extraPmt2:
    hoa = st.number_input("Estimated HOA fee:", value=250,
        step=50, min_value = 0)
with extraPmt3:
    utilities = st.number_input("Estimated utilities costs:", value=300,
        step=50, min_value = 0)
total_non_equity_costs = round((utilities + hoa + (taxes / 12)) + abs(payment), 2)

st.subheader(f"${abs(total_non_equity_costs)} per month payment with the extra costs included")

# Create a couple of menu items for user to specify their investment as a landlord
is_renting = st.checkbox("Do you plan on renting it out?")
after_n_months = False
landlord_expenses = 0
if is_renting:
    landlord_column1, landlord_column2 = st.columns(2)
    with landlord_column1:
        after_n_months = int(st.number_input('After how many months will you start renting it out?',
                                             min_value=1,
                                             max_value=360,  # or another appropriate maximum value
                                             value=60,
                                             step=1))
    with landlord_column2:
        landlord_expenses = st.number_input('Estimated Annual Landlord Costs?',
                                            min_value=0.00,
                                            value=6000.00,
                                            step=1500.00) / 12

st.subheader(f"Here's what that'll look like over the next {years} years")
schedule1, stats1, is_renting = amortization_table(yearly_interest_rate,
                                                   years,
                                                   loan_amount,
                                                   payment,
                                                   is_renting=is_renting,
                                                   after_n_months=after_n_months,
                                                   landlord_expenses=landlord_expenses)

if is_renting == True:
    plotly1 = px.line(schedule1,
        x = 'Payment_Date',
        y = ['Total Interest Paid', 'Total Principal Owned',
        'Total Paid to Bank','Total Paid by You Specifically'],
        title="Cumulative Interest and Principal over time")
else:
    plotly1 = px.line(schedule1,
        x = 'Payment_Date',
        y = ['Total Interest Paid', 'Total Principal Owned', 'Total Paid to Bank'],
        title="Cumulative Interest and Principal over time")

st.plotly_chart(plotly1)
st.dataframe(schedule1)
st.dataframe(stats1)

st.download_button('Download Amortization Data', schedule1.to_csv())
