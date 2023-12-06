# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 14:18:52 2021

@author: Irene
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import random
import time

from pyomo.environ import *

def unit_ranges(start_units, U, G, L, labels):
    units_range_index = pd.MultiIndex.from_product([range(U), range(L), labels.values()], names=('unit', 'time', 'node'))
    units_range_time = pd.DataFrame(index=units_range_index, columns=['inrange'])

    for u in range(U):
        for t in range(L):
            neighbors = list(nx.single_source_shortest_path_length(G, source=start_units[u], cutoff=t).keys())
            for neighbor in neighbors:
                units_range_time.loc[(u, t, labels[neighbor])]['inrange'] = 1

    units_range_time = units_range_time.fillna(0)

    #return np.squeeze(units_range_time).to_dict()
    return units_range_time

def optimization(G, U, routes_time_nodes, units_range_time, R, V, T, labels):
    
    # Create model
    model = ConcreteModel('FIP_pyomo_MH') 
    
    model.units = Set(initialize=range(U), ordered=True)
    model.routes = Set(initialize=range(R), ordered=True)
    model.T = Set(initialize=range(T), ordered=True)
    model.vertices = Set(initialize=[i for i in labels.values()], ordered=True) #or just range(V)?
    #model.vertices = Set(initialize=range(V), ordered=True)
    #alpha_rtv = routes_time_nodes.to_numpy().reshape((R,T,V))
    #tau_utv = units_range_time.to_numpy().reshape((U,T,V))

    model.alpha_rtv = Param(model.routes, model.T, model.vertices, within=Binary, initialize=np.squeeze(routes_time_nodes).to_dict())
    model.tau_utv = Param(model.units, model.T, model.vertices, within=Binary, initialize=np.squeeze(units_range_time).to_dict())
    
    # Create variables
    model.Zr= Var(model.routes, within=Binary)
    model.pi_uv= Var(model.units, model.vertices, within=Binary)
    #model.z_rutv= Var(model.routes, model.units, model.T, model.vertices, within=Binary)
    model.limits= ConstraintList()
    
    #Zr = m.addVars(R,                       vtype=GRB.BINARY, name="Zr")    # routes intercepted
    #pi_uv = m.addVars(U, V,                  vtype=GRB.BINARY, name="pi_uv")
    #z_rutv = m.addVars(R, U, T, V,  vtype=GRB.BINARY, name="z_rutv")
    
    #Objective
    model.obj = Objective(sense=maximize, 
                          expr=sum(model.Zr[r] for r in model.routes))
    
    #m.setObjective(quicksum(Zr), GRB.MAXIMIZE)
    
    # max units constraint
    def maxunits_rule(model, u):
        return sum(model.pi_uv[u,v] for v in model.vertices) == 1  # <= for max units = U; == for place all units
    model.maxunits = Constraint(model.units, rule=maxunits_rule)

    # interception constraint
    def interception_rule(model, r):
        return model.Zr[r] <= sum(sum(sum(model.pi_uv[u,v] * model.alpha_rtv[r, t, v] * model.tau_utv[u,t,v]
                                          for v in model.vertices)
                                      for u in model.units)
                                  for t in model.T)
    model.interception = Constraint(model.routes, rule=interception_rule) 
    
    
    #opt = SolverFactory("gurobi", solver_io="python")
    #opt = SolverFactory('glpk')
    #opt = SolverFactory('solvers/glpsol.exe')
    # opt = SolverFactory('/home/isvandroffelaa/cbc/bin/cbc.exe')
    # opt = SolverFactory('solvers/cbc.exe')
    opt = SolverFactory('cbc')

    #time out after x seconds
    #opt.options['seconds'] = 120

    #solve
    results = opt.solve(model)
    
    #write results
    results.write(num=1)

    start_time = time.time()
    results = opt.solve(model)
    opt_time = time.time() - start_time
    
    routes_intercepted = {}
    for i in range(R):
        routes_intercepted[i] = model.Zr[i].value
    
    units_places = {}
    for u in range(U):
        for v in labels.values():
            units_places[(u,v)] = model.pi_uv[u,v].value
        
    #list of unit nodes from results
    list_unit_nodes = []
    for unit, presence in units_places.items():
        if presence == 1:
            unitnr, unitnode = unit
            list_unit_nodes.append(unitnode)   
            
    #print results
    num_intercepted = sum(1 for value in routes_intercepted.values() if value == 1)
    # print("pct of routes intercepted: ", (num_intercepted*100)/R, '%')
            
    return routes_intercepted, list_unit_nodes, opt_time