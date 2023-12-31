
import pandas as pd
import networkx as nx

# Load datasets
members = pd.read_csv("congress_members.csv")
edges = nx.read_edgelist("congress_edges.dat", create_using=nx.DiGraph())

summary_state = members.State.describe()
summary_party = members.Party.describe()
summary_chamber = members.Chamber.describe()
summary_missing = members.isnull().sum()

# Prepare report
data_size = f"Number of rows: {members.shape[0]}\nNumber of columns: {members.shape[1]}"
summary_statistics = f"State:\n{summary_state}\nParty:\n{summary_party}\nChamber:\n{summary_chamber}"
categorical_variables = f"Categorical columns: State, Party, Chamber\nMost common State: {summary_state.top}\nMost common Party: {summary_party.top}\nMost common Chamber: {summary_chamber.top}"
missing_values = f"Missing values:\n{summary_missing}"

report = f"# Data Size\n{data_size}\n\n# Summary Statistics\n{summary_statistics}\n\n# Categorical Variables\n{categorical_variables}\n\n# Missing Values\n{missing_values}"

with open("data_exploration.txt", 'w') as f:
       f.write(report)

# Network data
num_nodes = len(edges.nodes)
num_edges = len(edges.edges)
network_data = f"\n\n# Network Data\nNumber of nodes: {num_nodes}\nNumber of edges: {num_edges}"
with open("data_exploration.txt", 'a') as f:
    f.write(network_data)
