
import pandas as pd
import numpy as np
import networkx as nx

# Load the data
members = pd.read_csv('congress_members.csv')
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# Prepare output file
with open("data_exploration.txt", "w") as file:
    # Data Size
    file.write("# Data Size\n")
    file.write(f"Members data: {members.shape[0]} rows, {members.shape[1]} columns\n")
    file.write(f"Edges data: {edges.number_of_edges()} edges, {edges.number_of_nodes()} nodes\n\n")

    # Summary Statistics
    file.write("# Summary Statistics\n")
    # Exclude 'Handle' from summary statistics, it's unique value for each row
    for col in members.drop(columns=['Handle']).columns:
        file.write(f"{col}:\n")
        file.write(f"{members[col].describe()}\n\n")

    # Categorical Variables
    file.write("# Categorical Variables\n")
    # Exclude 'Handle' from categorical variables, it's unique value for each row
    for col in members.select_dtypes(include=['object']).drop(columns=['Handle']).columns:
        file.write(f"{col} (Top 5):\n")
        file.write(f"{members[col].value_counts().nlargest(5)}\n\n")

    # Missing Values
    file.write("# Missing Values\n")
    missing_flag = False
    for col in members.columns:
        missing = members[col].isnull().sum()
        if missing > 0:
            file.write(f"{col}: {missing}\n")
            missing_flag = True
    if not missing_flag:
        file.write("There are no missing values in the data.\n")
    file.write("\n")

    # Check the distribution of the number of engagements per member
    file.write("# Node Degree\n")
    degrees = [deg for node, deg in edges.degree()]
    file.write(f"Mean: {np.mean(degrees)}, Median: {np.median(degrees)}, Std: {np.std(degrees)}\n")
