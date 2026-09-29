# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 14:50:08 2026

@author: zinoh
"""

import pandas as pd

import pyomo.environ as pyo
model = pyo.ConcreteModel()

path = r"C:\Users\zinoh\OneDrive\Documents\Tube service optimisation\Victoria_mon.csv"

data = pd.read_csv(path)

data["t"] = pd.factorize(data["Time"])[0] + 1

data["Load"] = data["Load"].str.replace(",", "", regex=False).astype(int)


# create function of model

def solve_model(capacity):
    model = pyo.ConcreteModel()
    
    ## Sets
    model.LINKS = pyo.RangeSet(1, 15)
    model.TIMES = pyo.RangeSet(1, data["t"].max())
    model.DIRECTIONS = pyo.Set(initialize=["NB", "SB"])
    
    ## Parameters

    model.capacity = pyo.Param(initialize=capacity)

    model.Fleet = pyo.Param(initialize=47)

    Link_load_data = {
        (row["Link number"], row["t"], row["Dir"]): row["Load"]
        for _, row in data.iterrows()
    }

    model.Load = pyo.Param(model.LINKS, model.TIMES, model.DIRECTIONS,
                       initialize= Link_load_data)
    
    ## Variables

    model.x_TIMES = pyo.RangeSet(-2, data["t"].max())

    model.x = pyo.Var(model.x_TIMES, model.DIRECTIONS, 
                      domain = pyo.NonNegativeIntegers)

    for t in [-2]:
        for d in ["NB", "SB"]:
            model.x[t, d].fix(0)
            
    for t in [-1, 0]:
        for d in ["NB", "SB"]:
            model.x[t, d].fix(1)
            
    ## Constraints

    def NB_half_one_rule(model, i, t):
        return model.Load[i,t,"NB"] <= model.capacity * (
                model.x[t, "NB"] + model.x[t-2, "SB"])
            
    model.NB_half_one = pyo.Constraint(
        pyo.RangeSet(1,8), model.TIMES, rule = NB_half_one_rule)

    def NB_half_two_rule(model, i, t):
        return model.Load[i,t,"NB"] <= model.capacity * (
                model.x[t-1, "NB"] + model.x[t-3, "SB"])

    model.NB_half_two = pyo.Constraint(
        pyo.RangeSet(9,15), model.TIMES, rule = NB_half_two_rule)


    def SB_half_two_rule(model, i, t):
        return model.Load[i,t,"SB"] <= model.capacity * (
                model.x[t, "SB"] + model.x[t-2, "NB"])

    model.SB_half_two = pyo.Constraint(
        pyo.RangeSet(9,15), model.TIMES, rule = SB_half_two_rule)


    def SB_half_one_rule(model, i, t):
        return model.Load[i,t,"SB"] <= model.capacity * (
                model.x[t-1, "SB"] + model.x[t-3, "NB"])

    model.SB_half_one = pyo.Constraint(
        pyo.RangeSet(1,8), model.TIMES, rule = SB_half_one_rule)

    def fleet_rule(model,t):
        return sum(
            model.x[tau,"NB"] + model.x[tau,"SB"]
            for tau in range (t-3, t+1)
            ) <= model.Fleet

    model.fleet = pyo.Constraint(model.TIMES, rule = fleet_rule)

    def frequency_rule(model, t, d):
        return model.x[t, d] <= 9

    model.frequency = pyo.Constraint(model.TIMES, model.DIRECTIONS,
                                 rule = frequency_rule)
    
    ## Objective function

    def objective_rule(model):
        return sum(
            model.x[t,d] 
            for t in model.TIMES
            for d in model.DIRECTIONS
            )
    
    model.obj = pyo.Objective(rule = objective_rule, sense = pyo.minimize)
    
    # Solve
    
    opt = pyo.SolverFactory('highs')
    opt.solve(model)
    
    return model

capacities = [856, 749, 642, 535, 428]

# Minimised trains

results = []

for c in capacities:
    model = solve_model(c)
    
    results.append({
        "Capacity": c,
        "Minimised_trains":  pyo.value(model.obj)
        })
 
sensitivity_df = pd.DataFrame(results)

sensitivity_df.to_csv("Trains_Sensitivity.csv", index=False)

# Number of dispatches and active trains

rows1 = []

rows2 = []

for c in capacities:
    model = solve_model(c)
    
    for t in model.TIMES:
        rows1.append({
            "Capacity": c,
            "time": t,
            "NB": pyo.value(model.x[t, "NB"]),
            "SB": pyo.value(model.x[t, "SB"])
            })
        
    for t in model.TIMES:
        active = sum(
            pyo.value(model.x[tau, d])
            for tau in range(t-3, t+1)
            for d in model.DIRECTIONS
        )
        rows2.append({
            "Capacity": c,
            "time": t,
            "Trains_active": active
            })
    
df1 = pd.DataFrame(rows1)

df2 = pd.DataFrame(rows2)

df_merged = pd.merge(df1, df2, on=["time", "Capacity"], how="inner")  

intervals = data[["Time", "t"]].drop_duplicates()

Vic_Mon_Result = intervals.merge(df_merged, left_on = "t", 
                                 right_on = "time", how="left")

Vic_Mon_Result = Vic_Mon_Result.drop(columns = ["time"])

Vic_Mon_Result.to_csv("Victoria_Monday_Train_sensitivity.csv", index=False)



