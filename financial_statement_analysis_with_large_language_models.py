# -*- coding: utf-8 -*-
"""Financial_Statement_Analysis_with_Large_Language_Models.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1pY7DVcTMAoJUD8pOlT_KZlknqZ0Lg597

**Financial Statement Analysis with Large Language Models**

Tried to Implement:  https://bfi.uchicago.edu/wp-content/uploads/2024/05/BFI_WP_2024-65.pdf
"""

import requests
import pandas as pd
import openai
import os
from openai import OpenAI

from google.colab import userdata
openai_key = userdata.get('openai_key')
financialmodelingprep_key = userdata.get('fin_data')

os.environ["OPENAI_API_KEY"] = openai_key

# fitching financial data
# https://site.financialmodelingprep.com/developer/docs#income-statements-financial-statements


def get_financial_data(ticker, data_type):
    base_url = 'https://financialmodelingprep.com/api'
    api_key = financialmodelingprep_key
    url = f'{base_url}/v3/{data_type}/{ticker}?period=annual&apikey={api_key}'

    try:
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}")

        data = response.json()

        if not data or 'error' in data:
            raise ValueError(f"No data found for ticker {ticker} or the API returned an error: {data.get('error', 'Unknown error')}")

        df = pd.DataFrame(data)

        try:
            df.to_csv(f'{ticker}_{data_type}_data.csv', index=False)
        except Exception as e:
            raise Exception(f"Error saving data to CSV: {e}")

        return df

    except requests.exceptions.RequestException as e:
        print(f"Request exception occurred: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

balance_sheet = get_financial_data('AAPL', 'balance-sheet-statement')
income_statement = get_financial_data('AAPL', 'income-statement')
cash_flow = get_financial_data('AAPL', 'cash-flow-statement')

def std_financial_data(df):
    if df is None or df.empty:
        raise ValueError("Input DataFrame is empty or None.")
    dfc = df.copy()

    if 'calendarYear' not in dfc.columns:
        raise KeyError("'calendarYear' column is missing from the input DataFrame.")

    dfc['calendarYear'] = pd.to_numeric(dfc['calendarYear'], errors='coerce')

    if dfc['calendarYear'].isna().any():
        raise ValueError("There are invalid or missing values in 'calendarYear' after conversion.")

    current_year = dfc['calendarYear'].max()

    if pd.isna(current_year) or current_year < 1900:
        raise ValueError(f"Invalid current year: {current_year} found in 'calendarYear'.")

    dfc['calendarYear'] = dfc['calendarYear'].apply(
        lambda x: f"t-{current_year - x}" if x < current_year else "t"
    )

    columns_to_remove = ['cik', 'symbol', 'fillingDate', 'acceptedDate', 'calendarYear', 'link', 'finalLink']
    missing_columns = [col for col in columns_to_remove if col not in dfc.columns]

    if missing_columns:
        raise KeyError(f"The following columns are missing from the DataFrame: {', '.join(missing_columns)}")

    dfc = dfc.drop(columns=columns_to_remove)

    dfc.columns = dfc.columns.str.lower().str.replace(' ', '_')

    return dfc


try:
    balance_sheet_processed = std_financial_data(balance_sheet)
    income_statement_processed = std_financial_data(income_statement)
    cash_flow_processed = std_financial_data(cash_flow)
    print("Data processing completed successfully.")
except ValueError as e:
    print(f"ValueError: {e}")
except KeyError as e:
    print(f"KeyError: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

def calculate_financial_ratios(df):
    dfc = df.copy()

    dfc['current_ratio'] = dfc['totalcurrentassets'] / dfc['totalcurrentliabilities']
    dfc['quick_ratio'] = (dfc['cashandcashequivalents'] + dfc['shortterminvestments'] + dfc['netreceivables']) / dfc['totalcurrentliabilities']

    dfc['debt_to_equity_ratio'] = dfc['totalliabilities'] / dfc['totalstockholdersequity']
    dfc['debt_ratio'] = dfc['totalliabilities'] / dfc['totalassets']
    dfc['net_debt_to_equity_ratio'] = (dfc['totaldebt'] - dfc['cashandcashequivalents']) / dfc['totalstockholdersequity']

    dfc['equity_ratio'] = dfc['totalstockholdersequity'] / dfc['totalassets']
    return dfc


def calculate_income_statement_ratios(df):
    dfc = df.copy()

    dfc['gross_profit_margin'] = dfc['grossprofit'] / dfc['revenue']
    dfc['operating_profit_margin'] = dfc['operatingincome'] / dfc['revenue']
    dfc['net_profit_margin'] = dfc['netincome'] / dfc['revenue']
    dfc['ebitda_margin'] = dfc['ebitda'] / dfc['revenue']

    dfc['eps'] = dfc['netincome'] / dfc['weightedaverageshsout']
    dfc['eps_diluted'] = dfc['netincome'] / dfc['weightedaverageshsoutdil']

    return dfc


def calculate_cash_flow_metrics(cash_flow_df, income_df=None, balance_df=None):
    df = cash_flow_df.copy()

    required_columns = ['netcashprovidedbyoperatingactivities', 'freecashflow',
                        'dividendspaid', 'netincome', 'investmentsinpropertyplantandequipment']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Missing necessary columns in cash flow data")

    if balance_df is not None:
        total_liabilities = balance_df['totalliabilities'].iloc[0]
        df['operating_cash_flow_ratio'] = df['netcashprovidedbyoperatingactivities'] / total_liabilities

    if income_df is not None:
        revenue = income_df['revenue'].iloc[0]
        df['cash_flow_margin'] = df['netcashprovidedbyoperatingactivities'] / revenue

    df['reinvestment_ratio'] = df['investmentsinpropertyplantandequipment'] / df['netcashprovidedbyoperatingactivities']

    df['dividend_payout_ratio'] = df['dividendspaid'] / df['freecashflow']

    if income_df is not None:
        df['fcf_to_revenue'] = df['freecashflow'] / revenue

    df['cash_conversion_efficiency'] = df['netcashprovidedbyoperatingactivities'] / df['netincome']

    return df


balance_sheet_with_ratios = calculate_financial_ratios(balance_sheet_processed)
income_statement_with_ratios = calculate_income_statement_ratios(income_statement_processed)
cash_flow_with_metrics = calculate_cash_flow_metrics(cash_flow_processed, income_statement_processed, balance_sheet_processed)

# Convert df to string format for model

def convert_to_string(dataframe):
    return dataframe.to_string(index=False)

income_statement_string = convert_to_string(income_statement_with_ratios)
balance_sheet_string = convert_to_string(balance_sheet_with_ratios)
cash_flow_string = convert_to_string(cash_flow_with_metrics)

#Chain-of-Thought (CoT) Prompt

def financial_analysis_cot(model, balance_sheet, income_statement, cash_flow):

    prompt = (
        "You are a financial analyst. Analyze the following financial data step-by-step to predict whether earnings will increase or decrease in the next period. Follow these steps:\n"
        "1. Identify key trends in the financial line items provided.\n"
        "2. Compute key financial ratios, including profitability, liquidity, leverage, and efficiency ratios.\n"
        "3. Provide a narrative interpretation of the computed ratios, focusing on their implications for financial performance.\n"
        "4. Based on the trends and ratio analysis, predict whether earnings will increase or decrease in the next period, and explain your reasoning clearly.\n"
        f"Balance Sheet:\n{balance_sheet}\n\n"
        f"Income Statement:\n{income_statement}\n\n"
        f"Cash Flow:\n{cash_flow}\n\n"
    )

    client = OpenAI()

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ],
        logprobs=True,
        top_p=1,
    )

    result = response.choices[0].message.content
    log_probs = response.choices[0].logprobs

    return {
        "analysis": result,
        "log_probs": log_probs
    }

model = "gpt-4o"
balance_sheet = balance_sheet_string
income_statement = income_statement_string
cash_flow = cash_flow_string

result = financial_analysis_cot(model, balance_sheet, income_statement, cash_flow)
print("Analysis:", result["analysis"])
print("Log Probabilities:", result["log_probs"])