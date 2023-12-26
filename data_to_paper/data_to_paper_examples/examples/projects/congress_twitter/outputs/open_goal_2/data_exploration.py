
import pandas as pd
import networkx as nx

# Reading the dataset
members = pd.read_csv('congress_members.csv')
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype=int)

# Lists for storing the analysed information
data_size = []
summary_statistics = []
categorical_variables = []
missing_values = []

# Data Size
data_size.append(f"Number of nodes (Congress members): {len(members)}")
data_size.append(f"Number of edges (Interactions between Congress members): {nx.number_of_edges(edges)}")

# Summary Statistics
node_degrees = [val for (node, val) in edges.degree()] 
summary_statistics.append("Node Degree Description:")
summary_statistics.append(pd.Series(node_degrees).describe().to_string())

# Categorical Variables
states_freq = members['State'].value_counts().idxmax()
parties_freq = members['Party'].value_counts().idxmax()
chambers_freq = members['Chamber'].value_counts().idxmax()

categorical_variables.append(f"The state with the most representatives: {states_freq}")
categorical_variables.append(f"The party with the most representatives: {parties_freq}")
categorical_variables.append(f"The chamber with the most representatives: {chambers_freq}")

# Missing Values
missing_values.append(f"Number of missing values in the data: {members.isnull().sum().sum()}") 

# Writing to data_exploration.txt
with open("data_exploration.txt", 'w') as f:
    f.write("# Data Size\n")
    f.write('\n'.join(data_size))
    f.write("\n\n# Summary Statistics\n")
    f.write('\n'.join(summary_statistics))
    f.write("\n\n# Categorical Variables\n")
    f.write('\n'.join(categorical_variables))
    f.write("\n\n# Missing Values\n")
    f.write('\n'.join(missing_values))
