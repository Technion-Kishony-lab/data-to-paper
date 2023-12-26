
import pandas as pd
import networkx as nx

# Load data
congress_members = pd.read_csv('congress_members.csv')
congress_edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# Initialize our text file
data_exploration = open("data_exploration.txt", 'w')

# Data Size
data_exploration.write("# Data Size\n")
data_exploration.write("Number of congress members: " + str(len(congress_members)) + "\n")
data_exploration.write("Number of edges in the graph: " + str(len(congress_edges.edges())) + "\n\n")

# Summary Statistics
data_exploration.write("# Summary Statistics\n")
data_exploration.write(congress_members.describe(include='all').to_string() + "\n\n")

# Categorical Variables
data_exploration.write("# Categorical Variables\n")
for column in congress_members.select_dtypes(include='object').columns:
    data_exploration.write(f'Most common values for {column}: {congress_members[column].value_counts().idxmax()}\n')
data_exploration.write("\n")

# Missing Values
data_exploration.write("# Missing Values\n")
missing_values = congress_members.isna().sum()
if missing_values.any():
    data_exploration.write(missing_values.to_string() + "\n")
else:
    data_exploration.write("There are no missing values in the data.\n")

data_exploration.close()
