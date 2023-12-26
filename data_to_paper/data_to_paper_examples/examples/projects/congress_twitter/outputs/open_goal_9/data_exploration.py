
import pandas as pd
import networkx as nx

# Load datasets
df = pd.read_csv('congress_members.csv')
G = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype=int)

# File to store the results
output_file = open("data_exploration.txt", "w")
 
# Data size
output_file.write("# Data Size\n")
output_file.write(f"Number of Members: {df.shape[0]}\n")
output_file.write(f"Number of Columns in Members Data: {df.shape[1]}\n")
output_file.write(f"Number of Edges: {G.number_of_edges()}\n")
output_file.write(f"Number of Nodes: {G.number_of_nodes()}\n")

# Summary Statistics
output_file.write("\n# Summary Statistics\n")
for column in df.columns:
    output_file.write(f"\n{column}: Number of Unique Values: {df[column].nunique()}")
output_file.write("\n")

# Categorical Variables
output_file.write("\n# Categorical Variables\n")
for col in df.select_dtypes(include=['object']).columns:
    output_file.write(f"\n{col}: {df[col].nunique()} unique values. Most frequent: {df[col].mode().values[0]}")
output_file.write("\n")

# Missing Values
output_file.write("\n# Missing Values\n")
output_file.write(df.isnull().sum().to_string()+ "\n")

# Other summary - Degree Centrality (helpful in understanding the influence of a node in a graph)
output_file.write("\n# Degree Centrality\n# Degree Centrality is a measure of the importance of a node in a graph.\n")

dc = nx.degree_centrality(G)

# Degree centrality for the 5 nodes having the highest degree centrality
max_dc = dict(sorted(dc.items(), key=lambda item: item[1], reverse=True)[:5])
output_file.write("Top 5 nodes having the highest degree centrality and their Handles: \n")
for key, value in max_dc.items():
    output_file.write(f"{key} ({df.iloc[key]['Handle']}): {value:0.2f}\n")

# Degree centrality for 5 nodes having the lowest degree centrality
min_dc = dict(sorted(dc.items(), key=lambda item: item[1])[:5])
output_file.write("\nBottom 5 nodes having the lowest degree centrality and their handles: \n")
for key, value in min_dc.items():
    output_file.write(f"{key} ({df.iloc[key]['Handle']}): {value:0.2f}\n")

output_file.close()
