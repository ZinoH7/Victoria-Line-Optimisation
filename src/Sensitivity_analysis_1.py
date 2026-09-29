# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 15:29:23 2026

@author: zinoh
"""
import pandas as pd

import pyomo.environ as pyo
model = pyo.ConcreteModel()

from pyomo.environ import *
from pyomo.environ import ConcreteModel, Param, Var, Constraint, value
model = ConcreteModel()

data = pd.read_csv("data/processed/data_cleaned.csv")

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

    model.capacity = Param(initialize= capacity)
    model.Fleet = Param(initialize=47)

    Link_load_data = {
        (row["Link number"], row["t"], row["Dir"]): row["Load"]
        for _, row in data.iterrows()
    }

    model.Load = Param(model.LINKS, model.TIMES, model.DIRECTIONS,
                       initialize= Link_load_data)
    
    ## Variables

    model.x_TIMES = pyo.RangeSet(-2, data["t"].max())

    model.x = Var(model.x_TIMES, model.DIRECTIONS, domain = pyo.NonNegativeIntegers)

    # Trains before start

    for t in [-2]:
        for d in ["NB", "SB"]:
            model.x[t, d].fix(0)
            
    for t in [-1, 0]:
        for d in ["NB", "SB"]:
            model.x[t, d].fix(1)

    model.O = Var(model.LINKS, model.TIMES, model.DIRECTIONS, 
                  domain = pyo.NonNegativeIntegers)
    
    ## Constraints

    def NB_half_one_rule(model, i, t):
        return model.O[i,t,"NB"] >= (
                model.Load[i,t,"NB"] - model.capacity * (
                model.x[t, "NB"] + model.x[t-2, "SB"])
                )


    model.NB_half_one = Constraint(
        pyo.RangeSet(1,8), model.TIMES, rule = NB_half_one_rule)


    def NB_half_two_rule(model, i, t):
        return model.O[i,t,"NB"] >= (
                model.Load[i,t,"NB"] - model.capacity * (
                model.x[t-1, "NB"] + model.x[t-3, "SB"])
                )


    model.NB_half_two = Constraint(
        pyo.RangeSet(9,15), model.TIMES, rule = NB_half_two_rule)


    def SB_half_two_rule(model, i, t):
        return model.O[i,t,"SB"] >= (
                model.Load[i,t,"SB"] - model.capacity * (
                model.x[t, "SB"] + model.x[t-2, "NB"])
                )


    model.SB_half_two = Constraint(
        pyo.RangeSet(9,15), model.TIMES, rule = SB_half_two_rule)


    def SB_half_one_rule(model, i, t):
        return model.O[i,t,"SB"] >= (
                model.Load[i,t,"SB"] - model.capacity * (
                model.x[t-1, "SB"] + model.x[t-3, "NB"])
                )

    model.SB_half_one = Constraint(
        pyo.RangeSet(1,8), model.TIMES, rule = SB_half_one_rule)

    def fleet_rule(model,t):
        return sum(
            model.x[tau,"NB"] + model.x[tau,"SB"]
            for tau in range (t-3, t+1)
            ) <= model.Fleet

    model.fleet = Constraint(model.TIMES, rule = fleet_rule)
    
    def frequency_rule(model, t, d):
        return model.x[t, d] <= 9

    model.frequency = Constraint(model.TIMES, model.DIRECTIONS,
                                 rule = frequency_rule)

    ## Objective function

    def objective_rule(model):
        return sum(
            model.O[i,t,d] 
            for i in model.LINKS
            for t in model.TIMES
            for d in model.DIRECTIONS
            )

    model.obj = pyo.Objective(rule = objective_rule, sense = pyo.minimize)
    
    # Solve
    
    opt = SolverFactory('glpk')
    opt.solve(model)
    
    return model

capacities = [856, 749, 642, 535, 428]

# Minimised overcrowding

results = []

for c in capacities:
    model = solve_model(c)
    
    results.append({
        "Capacity": c,
        "Minimised overcrowding":  value(model.obj)
        })
 
sensitivity_df = pd.DataFrame(results)


# Num ber of dispatches and active trains

rows1 = []

rows2 = []

for c in capacities:
    model = solve_model(c)
    
    for t in model.TIMES:
        rows1.append({
            "Capacity": c,
            "time": t,
            "NB": value(model.x[t, "NB"]),
            "SB": value(model.x[t, "SB"])
            })
        
    for t in model.TIMES:
        active = sum(
            value(model.x[tau, d])
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

Vic_Mon_Result.to_csv("data/processed/Sensitivity_m1.csv", index=False)

