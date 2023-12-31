
import pandas as pd
import numpy as np
import scipy
import networkx as nx

# Load data
members_df = pd.read_csv("congress_members.csv")
edges_df = pd.read_table("congress_edges.dat", delimiter=" ", names=("Source", "Target"))

# Open output txt file
file = open("data_exploration.txt", "w")

# Data size
file.write("# Data Size\n")
file.write(f"Rows in congress_members: {len(members_df)}\n")
file.write(f"Columns in congress_members: {len(members_df.columns)}\n")
file.write(f"Rows in congress_edges: {len(edges_df)}\n")
file.write(f"Columns in congress_edges: {len(edges_df.columns)}\n")

# Summary statistics - for now we can only do this for the 'edges' data
file.write("# Summary Statistics\n")
description = edges_df.describe()
file.write(f"{description}\n")

# Categorical Variables - assume 'State', 'Party', 'Chamber' are the only categorical variables
file.write("# Categorical Variables\n")
for column in ['State', 'Party', 'Chamber']:
    file.write(f"{column} values and counts: {members_df[column].value_counts().to_string()}\n")

# Checking for Missing Values
file.write("# Missing Values\n")
file.write(f"Missing values in congress_members: {members_df.isnull().sum().to_string()}\n")
file.write(f"Missing values in congress_edges: {edges_df.isnull().sum().to_string()}\n")

# Closing the file
file.close()
