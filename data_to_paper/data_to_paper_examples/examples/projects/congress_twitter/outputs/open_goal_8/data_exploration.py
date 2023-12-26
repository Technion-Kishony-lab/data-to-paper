
import pandas as pd
import networkx as nx

# Reading and parsing the files
members_df = pd.read_csv('congress_members.csv')
edges_df = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype= int)

# Data exploration
with open('data_exploration.txt', 'w') as textfile:
    # Data Size
    textfile.write("# Data Size \n")
    textfile.write(f"Number of congress members (nodes): {members_df.shape[0]}\n")
    textfile.write(f"Number of interactions (edges): {edges_df.size()}\n")
    textfile.write(f"Number of columns in members data: {members_df.shape[1]}\n\n")

    # Summary Statistics
    textfile.write("# Summary Statistics\n")
    textfile.write(f"Number of unique states: {members_df['State'].nunique()}\n")
    textfile.write(f"Number of unique parties: {members_df['Party'].nunique()}\n")
    textfile.write(f"Number of unique chambers: {members_df['Chamber'].nunique()}\n\n")

    # Categorical Variables
    textfile.write("# Categorical Variables\n")
    textfile.write(f"Most common state: {members_df['State'].mode().values[0]}\n")
    textfile.write(f"Most common party: {members_df['Party'].mode().values[0]}\n")
    textfile.write(f"Most common chamber: {members_df['Chamber'].mode().values[0]}\n\n")
    
    # Missing Values
    textfile.write("# Missing Values\n")
    textfile.write(f"Number of missing values in members data: \n{members_df.isnull().sum()}\n\n")
    textfile.write(f"Number of missing nodes in edges data: {len(set(range(members_df.shape[0])) - set(edges_df.nodes))}\n\n")
