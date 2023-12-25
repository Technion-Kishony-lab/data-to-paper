
import pandas as pd
import networkx as nx
import numpy as np

# Read in the members file with pandas
df_members = pd.read_csv('congress_members.csv')

# Gathering the Data Size information
data_size = f'Number of Members: {df_members.shape[0]}\nNumber of Columns in Members Data: {df_members.shape[1]}'

# Gathering the Summary Statistics information
summary_stats = df_members.describe(include='all').to_string()

# Gathering the Categorical Variables information
cats = df_members.select_dtypes(include=['object'])
freq_cats = cats.apply(lambda x: f"{x.name}: {x.value_counts().idxmax()} (Most Common)\n").to_list()

# Gathering the Missing Values information
missing_values_counts = df_members.isna().sum().sum()

# Read in the edges file with networkx
G = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())
num_of_edges = G.number_of_edges()
num_of_nodes = G.number_of_nodes()

# Write out the gathered data to a text file
with open('data_exploration.txt', 'w') as f:
    f.write('# Data Size\n')
    f.write(data_size)

    # Add number of edges and nodes
    f.write(f'\nNumber of Edges: {num_of_edges}\nNumber of Nodes: {num_of_nodes}\n')

    f.write('\n# Summary Statistics\n')
    f.write(summary_stats)

    f.write('\n# Categorical Variables\n')
    f.writelines(freq_cats)

    f.write('\n# Missing Values\n')
    f.write(f'Total Missing Values: {missing_values_counts}\n')
