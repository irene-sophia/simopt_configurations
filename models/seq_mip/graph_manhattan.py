# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 11:50:15 2021

@author: Irene
"""

import networkx as nx


def graph(N):
    """
    Generate manhattan graph
    
    Parameters
    ----------
    N : int
        width of graph.

    Returns
    -------
    G : networkx graph
        graph of size (N,N).
    labels : dict
        {pos: vertex number}.
    pos : dict
        {vertex:pos}.

    """    
    
    G = nx.grid_2d_graph(N,N)
    pos = dict( (n, n) for n in G.nodes() )
    labels = dict( ((i, j), i * N + j) for i, j in G.nodes() ) # 

    # set travel time (unidistant)
    travel_time = 1
    nx.set_edge_attributes(G, travel_time, "travel_time")

    return G, labels, pos