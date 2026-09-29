# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 15:57:08 2026

@author: zinoh
"""

# data cleaning

import pandas as pd

data = pd.read_csv("data/raw/Link_Loads.csv", skiprows=2)

data = data.drop(columns = ["Link", "From NLC", "From ASC",
                          "To NLC", "To ASC", "Early", "AM Peak", "Midday",
                          "PM Peak", "Evening", "Late"])

victoria = data.loc[data["Line"]=="Victoria"]

time_columns = victoria.columns[5:]

victoria_long = pd.melt(victoria, id_vars=["Line", "Dir", "Order", "From Station",
                                            "To Station", "Total"], 
                         value_vars=time_columns, 
                         var_name='Time', 
                         value_name='Load')

victoria_long.head()

# Adjust Order to link numbers - fine for NB but need reversing for SB

victoria_long.rename(columns={"Order":"Link number"}, inplace = True)

victoria_long.loc[
    victoria_long["Dir"] == "SB", "Link number"] = 16 - victoria_long.loc[
        victoria_long["Dir"] == "SB", "Link number"]


victoria_LP = victoria_long.drop(columns=["Line", "From Station", 
                                          "To Station", "Total"])

victoria_LP.to_csv("data/processed/data_cleaned.csv", index = False)
