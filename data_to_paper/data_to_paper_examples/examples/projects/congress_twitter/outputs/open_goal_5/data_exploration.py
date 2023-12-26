
import pandas as pd
import networkx as nx
import numpy as np

# Load data
congress_members = pd.read_csv('congress_members.csv')
congress_edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype=int)

# Get Stats
num_nodes = nx.number_of_nodes(congress_edges)
num_edges = nx.number_of_edges(congress_edges)

# Variables
state_counts = congress_members.State.value_counts()
party_counts = congress_members.Party.value_counts()
chamber_counts = congress_members.Chamber.value_counts()

# Missing Values 
missing_values = congress_members.isnull().sum()

# Write to File
with open('data_exploration.txt', 'w') as file:
    file.write("# Data Size\n")
    file.write(f"Number of Nodes: {num_nodes}\n")
    file.write(f"Number of Edges: {num_edges}\n")
    file.write("\n# Summary Statistics\n")
    file.write(f"Congress Members: {len(congress_members)}\n")
    file.write("\n# Categorical Variables\n")
    file.write(f"State:\n{state_counts}\n")
    file.write(f"Party:\n{party_counts}\n")
    file.write(f"Chamber:\n{chamber_counts}\n")
    file.write("\n# Missing Values\n")
    file.write(f"Missing Values:\n{missing_values}\n")
