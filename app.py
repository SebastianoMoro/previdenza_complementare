import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta

# Title and Description
st.title("Fondo Pensione vs. Investimento in conto titoli tassato")
st.markdown("""
### Introduzione
""")

# Sidebar for User Inputs
st.sidebar.header("Upload Files")
bond_file = st.sidebar.file_uploader("Upload bond.csv", type="csv")
stock_file = st.sidebar.file_uploader("Upload stock.csv", type="csv")

# Additional Inputs
st.sidebar.header("Settings")

initial_investment_pf = st.sidebar.number_input("Initial Pension Fund Investment", value=5000)
marginal_tax_rate = st.sidebar.slider("Marginal tax rate icome", 0.0, 1.0, 0.5)
tax_rate_pf = st.sidebar.slider("Tax rate pension fund", 0.09, 0.15, 0.15)
initial_investment = initial_investment_pf * ( 1 - marginal_tax_rate)
stock_percentage = st.sidebar.slider("Stock Percentage", 0.0, 1.0, 0.5)
yield_5 = st.sidebar.number_input("5-Year Yield (%)", value=1.5) / 100
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2018-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2023-12-31"))

if bond_file and stock_file:
    # Load and preprocess data
    asset1 = pd.read_csv(bond_file, parse_dates=["Data"])
    asset1.NAV = asset1.NAV.astype(float)
    asset2 = pd.read_csv(stock_file, parse_dates=["Data"])
    asset2.NAV = asset2.NAV.astype(float)

    portfolio = pd.merge(asset1, asset2, on="Data", suffixes=("_1", "_2"))
    portfolio.set_index("Data", inplace=True)
    portfolio.index = pd.to_datetime(portfolio.index, format='%d/%m/%Y')
    portfolio = portfolio.sort_index(ascending=True)

    


    portfolio = portfolio[(portfolio.index >= pd.to_datetime(start_date,  format='%d/%m/%Y')) \
                          & (portfolio.index <= pd.to_datetime(end_date, format='%d/%m/%Y'))]

    # Initialize portfolio columns
    portfolio["N_SHARES_1"] = 0.0
    portfolio["N_SHARES_2"] = 0.0
    portfolio["AVERAGE_PRICE_1"] = 0.0
    portfolio["AVERAGE_PRICE_2"] = 0.0
    portfolio["TOTAL_PORTFOLIO"] = 0.0
    portfolio["TAX_PAID"] = 0.0
    portfolio["PENSION_FUND"] = np.nan
    portfolio["TAX_PAID_PF"] = 0.0

    # Initialize portfolio
    nav_1 = portfolio.iloc[0]["NAV_1"]
    nav_2 = portfolio.iloc[0]["NAV_2"]
    portfolio.iloc[0, portfolio.columns.get_loc("N_SHARES_1")] = initial_investment * (1 - stock_percentage) / nav_1
    portfolio.iloc[0, portfolio.columns.get_loc("N_SHARES_2")] = initial_investment * stock_percentage / nav_2
    portfolio.iloc[0, portfolio.columns.get_loc("AVERAGE_PRICE_1")] = nav_1
    portfolio.iloc[0, portfolio.columns.get_loc("AVERAGE_PRICE_2")] = nav_2
    portfolio.iloc[0, portfolio.columns.get_loc("TOTAL_PORTFOLIO")] = (
        portfolio.iloc[0, portfolio.columns.get_loc("N_SHARES_1")] * nav_1 +
        portfolio.iloc[0, portfolio.columns.get_loc("N_SHARES_2")] * nav_2
    )
    portfolio.iloc[0, portfolio.columns.get_loc("PENSION_FUND")] = initial_investment_pf
    portfolio.iloc[0, portfolio.columns.get_loc("TAX_PAID")] = initial_investment_pf * marginal_tax_rate


    # Process portfolio
    previous_day = portfolio.index[0]
    investment_pf = initial_investment_pf
    
    for index, row in portfolio.iloc[1:].iterrows():
        # Update shares and portfolio value
        portfolio.loc[index, "AVERAGE_PRICE_1"] = portfolio.loc[previous_day, "AVERAGE_PRICE_1"]
        portfolio.loc[index, "AVERAGE_PRICE_2"] = portfolio.loc[previous_day, "AVERAGE_PRICE_2"]
        portfolio.loc[index, "N_SHARES_1"] = portfolio.loc[previous_day, "N_SHARES_1"]
        portfolio.loc[index, "N_SHARES_2"] = portfolio.loc[previous_day, "N_SHARES_2"]
        portfolio.loc[index, "TOTAL_PORTFOLIO"] = (
            portfolio.loc[index, "NAV_1"] * portfolio.loc[index, "N_SHARES_1"] +
            portfolio.loc[index, "NAV_2"] * portfolio.loc[index, "N_SHARES_2"]
        )
        portfolio.loc[index, "PENSION_FUND"] = portfolio.loc[previous_day, "PENSION_FUND"]

        # Simulate rebalancing logic
        # Add your rebalancing logic here, as needed

        if index.is_quarter_start == True or \
        ( (index - timedelta(1)).is_quarter_start == True and (index - timedelta(1)).dayofweek == 6 or (index - timedelta(1)).is_year_start ) or \
           ( (index - timedelta(2)).is_quarter_start == True and (index - timedelta(2)).dayofweek == 5 or (index - timedelta(2)).is_year_start ) or \
                ( (index - timedelta(3)).is_quarter_start == True and (index - timedelta(3)).is_year_start ):
         
            w_1 = portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_1") ] * \
                        portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_1") ] / \
                            portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("TOTAL_PORTFOLIO")]        

            
            w_2 = portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_2") ] * \
                        portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_2") ] / \
                            portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("TOTAL_PORTFOLIO")]
            
            
            n_bond_to_sell = ( w_1 - ( 1 - stock_percentage ) )/ ( 1 - stock_percentage ) * \
                                portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_1") ]
            
            
            
            n_stock_to_sell = ( w_2 - stock_percentage )/stock_percentage * \
                                portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_2") ]
            
            
            if n_stock_to_sell > 0:

                portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_2") ] = \
                    portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_2") ] - n_stock_to_sell
                
                net_filter =  ( portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_2") ]/ \
                            portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("AVERAGE_PRICE_2")] -  1 ) * 0.74 + 1
                tax_filter = ( portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_2") ]/ \
                            portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("AVERAGE_PRICE_2")] -  1 ) * 0.26
                
                tax_paid = n_stock_to_sell * portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_2") ] * tax_filter

                cash = n_stock_to_sell * portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_2") ] * net_filter

                n_bond_to_buy = cash / portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_1") ]

                portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("AVERAGE_PRICE_1")] = \
                    ( portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("AVERAGE_PRICE_1")] * \
                        portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_1") ] + \
                            portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_1")] * \
                                n_bond_to_buy ) / (n_bond_to_buy + portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_1") ] )
                
                
                portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_1") ] = \
                    portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_1") ] + n_bond_to_buy
                
                portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("TAX_PAID") ] = tax_paid

            if n_bond_to_sell > 0:

                portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_1") ] = \
                    portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_1") ] - n_bond_to_sell
                
                net_filter =  ( portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_1") ]/ \
                            portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("AVERAGE_PRICE_1")] -  1 ) * 0.74 + 1
                tax_filter = ( portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_1") ]/ \
                            portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("AVERAGE_PRICE_1")] -  1 ) * 0.26
                
                tax_paid = n_bond_to_sell * portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_1") ] * tax_filter

                cash = n_bond_to_sell * portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_1") ] * net_filter

                n_stock_to_buy = cash / portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_2") ]

                portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("AVERAGE_PRICE_2")] = \
                    ( portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("AVERAGE_PRICE_2")] * \
                        portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_2") ] + \
                            portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("NAV_2")] * \
                                n_stock_to_buy ) / (n_stock_to_buy + portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_2") ] )
                
                
                portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_2") ] = \
                    portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("N_SHARES_2") ] + n_stock_to_buy
                
                portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("TAX_PAID") ] = tax_paid

        if ((index - timedelta(1)).is_year_start and (index - previous_day).days != 1) or \
            ((index - timedelta(2)).is_year_start and (index - previous_day).days != 1) or \
                    ((index - timedelta(3)).is_year_start and (index - previous_day).days != 1):
            
            
            portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("PENSION_FUND") ] = investment_pf*(1+yield_5)

            portfolio.iloc[portfolio.index.get_loc(index), portfolio.columns.get_loc("TAX_PAID_PF") ] = investment_pf*(yield_5 - yield_5/1.20)

            investment_pf = investment_pf*(1+yield_5)     


        previous_day = index
    
    portfolio.iloc[-1, portfolio.columns.get_loc("PENSION_FUND") ] = investment_pf*(1+yield_5)

    portfolio.iloc[-1, portfolio.columns.get_loc("TAX_PAID_PF") ] = investment_pf*(yield_5 - yield_5/1.20 )

    df_self = portfolio.groupby(portfolio.index.year).sum()[["TAX_PAID"]].T

    df_self["TOTAL"] = portfolio.groupby(portfolio.index.year).sum()[["TAX_PAID"]].sum()

    df_self.loc["UNREALIZED_TAX", "TOTAL"] = max (portfolio.iloc[-1, portfolio.columns.get_loc("NAV_1")] - \
                                        portfolio.iloc[-1, portfolio.columns.get_loc("AVERAGE_PRICE_1")] , 0 ) * \
                                            portfolio.iloc[-1, portfolio.columns.get_loc("N_SHARES_1")]*0.26 + \
                                                max (portfolio.iloc[-1, portfolio.columns.get_loc("NAV_2")] - \
                                                    portfolio.iloc[-1, portfolio.columns.get_loc("AVERAGE_PRICE_2")] , 0 ) * \
                                                        portfolio.iloc[-1, portfolio.columns.get_loc("N_SHARES_2")]*0.26

    df_self.loc["NET_GAIN", "TOTAL" ] = max (portfolio.iloc[-1, portfolio.columns.get_loc("NAV_1")] - \
                                        portfolio.iloc[-1, portfolio.columns.get_loc("AVERAGE_PRICE_1")] , 0 ) * \
                                            portfolio.iloc[-1, portfolio.columns.get_loc("N_SHARES_1")]*0.74 + \
                                                max (portfolio.iloc[-1, portfolio.columns.get_loc("NAV_2")] - \
                                                    portfolio.iloc[-1, portfolio.columns.get_loc("AVERAGE_PRICE_2")] , 0 ) * \
                                                        portfolio.iloc[-1, portfolio.columns.get_loc("N_SHARES_2")]*0.74

    df_self.loc["INITIAL_WEALTH", "TOTAL"] = initial_investment

    df_self.loc["TOTAL", "TOTAL"] = df_self["TOTAL"].sum()


    df_self = df_self.round(decimals = 2).fillna("-")

    df_pf = portfolio.groupby(portfolio.index.year).sum()[["TAX_PAID_PF"]].T

    df_pf["TOTAL"] = portfolio.groupby(portfolio.index.year).sum()[["TAX_PAID_PF"]].sum()



    df_pf.loc["UNREALIZED_TAX", "TOTAL"] = initial_investment_pf*tax_rate_pf

    df_pf.loc["NET_GAIN", "TOTAL" ] = portfolio.iloc[-1, portfolio.columns.get_loc("PENSION_FUND") ] \
        - initial_investment_pf - df_pf.loc["UNREALIZED_TAX", "TOTAL"]

    df_pf.loc["INITIAL_WEALTH", "TOTAL"] = initial_investment_pf 

    df_pf.loc["TOTAL", "TOTAL"] = df_pf["TOTAL"].sum()

    print(df_pf)


    df_pf = df_pf.round(decimals = 2).fillna("-")
        

    # Display processed portfolio
    #st.write("Processed Portfolio Data:", portfolio)

    # Visualization
    fig, ax = plt.subplots()
    portfolio["TOTAL_PORTFOLIO"].plot(ax=ax, label="Total Portfolio Value")
    portfolio["PENSION_FUND"].plot(ax=ax, label="Pension Fund Value")
    ax.set_title("Portfolio Performance")
    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    ax.legend()
    st.pyplot(fig)

    st.write("Fondo pensione",df_pf)
    st.write("Investimento conto titoli",df_self)


else:
    st.warning("Please upload both bond.csv and stock.csv files to proceed.")

# Footer
st.markdown("---")
st.markdown("Developed with ❤️ using Streamlit.")
