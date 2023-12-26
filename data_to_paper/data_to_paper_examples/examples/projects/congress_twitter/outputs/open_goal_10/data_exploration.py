
import pandas as pd
import networkx as nx

#Loading data
df_members = pd.read_csv("congress_members.csv")
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype=int)

#Prepare for summary
summary = {}

summary["# Data Size"] = {}
summary["# Data Size"]["Number of Members"] = df_members.shape[0] #No of rows in df_members
summary["# Data Size"]["Number of Interaction Edges"] = edges.number_of_edges()

summary["# Summary Statistics"] = {}
summary["# Summary Statistics"]["Average No. Edges per Node"] = round(edges.number_of_edges()/edges.number_of_nodes(), 2)

summary["# Categorical Variables"] = {}
summary["# Categorical Variables"]["States Distribution"] = df_members["State"].value_counts().to_dict()
summary["# Categorical Variables"]["Party Distribution"] = df_members["Party"].value_counts().to_dict()
summary["# Categorical Variables"]["Chamber Distribution"] = df_members["Chamber"].value_counts().to_dict()

summary["# Missing Values"] = df_members.isna().sum().to_dict()

# Writing to output file
with open('data_exploration.txt', 'w') as f:
    for section, content in summary.items():
        f.write(f"{section}\n")
        if isinstance(content, dict):
            for key, value in content.items():
                f.write(f"{key}: {value}\n")
        else:
            f.write(f"{content}\n")
        f.write("\n")
