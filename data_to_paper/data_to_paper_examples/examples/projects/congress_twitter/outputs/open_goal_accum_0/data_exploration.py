
import pandas as pd
import numpy as np
import networkx as nx

# load the data
members_df = pd.read_csv('congress_members.csv')
edges_df = pd.read_csv('congress_edges.dat', sep=" ", names=["nodeFrom", "nodeTo"])
G = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# create the file
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write("# Data Size\n")
    f.write(f"Number of rows in 'congress_members.csv': {members_df.shape[0]}\n")
    f.write(f"Number of columns in 'congress_members.csv': {members_df.shape[1]}\n")
    f.write(f"Number of rows (edges) in 'congress_edges.dat': {edges_df.shape[0]}\n")
    f.write(f"Number of nodes in the graph: {G.number_of_nodes()}\n")
    f.write(f"Number of edges in the graph: {G.number_of_edges()}\n")

    # Summary Statistics
    f.write("\n# Summary Statistics\n")
    f.write("Not Applicable\n")

    # Categorical Variables
    f.write("\n# Categorical Variables\n")
    for col in ['State', 'Party', 'Chamber']:
        f.write(f"For variable '{col}' the most common value is: {members_df[col].mode()[0]}\n")

    # Missing Values
    f.write("\n# Missing Values\n")
    f.write(f"Missing values in 'congress_members.csv':\n{members_df.isnull().sum().to_string()}\n")
    f.write(f"Missing values in 'congress_edges.dat':\n{edges_df.isnull().sum().to_string()}\n")

f.close()
