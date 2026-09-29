# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:05:17 2026

@author: zinoh
"""

import pandas as pd

data = pd.read_csv("data/processed/data_cleaned.csv")

data["t"] = pd.factorize(data["Time"])[0] + 1

data["Load"] = data["Load"].str.replace(",", "", regex=False).astype(int)


import pyomo.environ as pyo
model = pyo.ConcreteModel()

from pyomo.environ import *
from pyomo.environ import ConcreteModel, Param, Var, Constraint, value
model = ConcreteModel()

## Sets
model.LINKS = pyo.RangeSet(1, 15)
model.TIMES = pyo.RangeSet(1, data["t"].max())
model.DIRECTIONS = pyo.Set(initialize=["NB", "SB"])

## Parameters

# Capacity
model.capacity = Param(initialize=856, mutable=True)

# Fleet Size
model.Fleet = Param(initialize=47, mutable=True)

# Link Load

Link_load_data = {
    (row["Link number"], row["t"], row["Dir"]): row["Load"]
    for _, row in data.iterrows()
}

model.Load = Param(model.LINKS, model.TIMES, model.DIRECTIONS,
                   initialize= Link_load_data)

## Variables

model.x_TIMES = pyo.RangeSet(-2, data["t"].max())

model.x = Var(model.x_TIMES, model.DIRECTIONS, domain = pyo.NonNegativeIntegers)

# Assume 4 trains are already circulating at the start
# One train in each half of each direction

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

print("Number of variables:", model.nvariables())
print("Number of constraints:", model.nconstraints())

## Solve

opt = SolverFactory('glpk')
opt.solve(model) 

print("Minimised overcrowding value:", value(model.obj))
    
rows1 = []

for t in model.TIMES:
    rows1.append({
        "time": t,
        "NB": value(model.x[t, "NB"]),
        "SB": value(model.x[t, "SB"])
        })       

df1 = pd.DataFrame(rows1)
print(df1)            


rows2 = []

# Assume 4 trains running at start

for t in model.TIMES:
    active = sum(
        value(model.x[tau, d])
        for tau in range(t-3, t+1)
        for d in model.DIRECTIONS
    )
    rows2.append({
        "time": t,
        "Trains_active": active
        })

df2 = pd.DataFrame(rows2)
print(df2) 

# join dfs

df_merged = pd.merge(df1, df2, on=["time"], how="inner")

print(df_merged["Trains_active"].max())
# fleet constraint is not binding

intervals = data[["Time", "t"]].drop_duplicates()

Vic_Mon_Result = intervals.merge(df_merged, left_on = "t", 
                                 right_on = "time", how="left")

Vic_Mon_Result = Vic_Mon_Result.drop(columns = ["time"])

Vic_Mon_Result.to_csv("data/processed/Optimised_m1_results.csv", index=False)
