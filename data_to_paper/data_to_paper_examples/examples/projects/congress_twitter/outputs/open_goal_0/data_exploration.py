
import pandas as pd
import networkx as nx
import numpy as np

# Load the data
members = pd.read_csv('congress_members.csv')
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype=int)

# Open the output file
with open("data_exploration.txt", "w") as file:

    file.write("# Data Size\n")
    file.write(f"Number of Congress members: {members.shape[0]}\n")
    file.write(f"Number of attributes per member: {members.shape[1]}\n")
    file.write(f"Number of edges (interactions): {edges.number_of_edges()}\n")

    file.write("\n# Summary Statistics\n")
    for col in members.columns:
        file.write(f"Statistics for {col}:\n")
        file.write(str(members[col].describe()) + "\n")

    file.write("\n# Categorical Variables\n")
    categorical_cols = members.select_dtypes(include='object').columns
    for col in categorical_cols:
        most_common = members[col].value_counts().idxmax()
        file.write(f"Most common {col}: {most_common}\n")

    file.write("\n# Missing Values\n")
    file.write(f"Number of missing or undefined values for each attribute:\n")
    file.write(str(members.isnull().sum()) + '\n')
    file.write(f"Do the numeric attributes have special categories that represent missing/unknown? {any(members.max() == np.inf)}\n")
