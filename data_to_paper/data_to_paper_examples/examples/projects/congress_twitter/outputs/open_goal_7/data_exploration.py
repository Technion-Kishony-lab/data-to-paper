
import pandas as pd
import numpy as np
import networkx as nx

# Read the data
congress_members = pd.read_csv("congress_members.csv")
edges = nx.read_edgelist("congress_edges.dat", create_using=nx.DiGraph())

# Data Size
num_nodes = len(congress_members)
num_edges = len(edges.edges())

# Summary Statistics
num_D = len(congress_members[congress_members['Party'] == 'D'])
num_R = len(congress_members[congress_members['Party'] == 'R'])
num_I = len(congress_members[congress_members['Party'] == 'I'])
num_House = len(congress_members[congress_members['Chamber'] == 'House'])
num_Senate = len(congress_members[congress_members['Chamber'] == 'Senate'])

# Categorical Variables
cat_vars = congress_members.select_dtypes('object').columns.values
most_common_values = {var: congress_members[var].value_counts().idxmax() for var in cat_vars}

# Missing Values
missing_values_count = congress_members.isnull().sum().to_dict()

# Open file to save summary
with open('data_exploration.txt', 'w') as f:
    f.write('# Data Size\n')
    f.write(f"Number of nodes (Congress members): {num_nodes}\n")
    f.write(f"Number of edges (Interactions): {num_edges}\n\n")

    f.write('# Summary Statistics\n')
    f.write(f"Number of Democrats: {num_D}\n")
    f.write(f"Number of Republicans: {num_R}\n")
    f.write(f"Number of Independents: {num_I}\n")
    f.write(f"Number of House members: {num_House}\n")
    f.write(f"Number of Senate members: {num_Senate}\n\n")

    f.write('# Categorical Variables\n')
    for var, common in most_common_values.items():                    
        f.write(f"{var}: most common value is {common}\n")
    
    f.write('# Missing Values\n')
    for var, count in missing_values_count.items():
        f.write(f"{var}: {count} missing values\n")
