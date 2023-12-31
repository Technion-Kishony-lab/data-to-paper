

# IMPORT
import pandas as pd
import numpy as np
import networkx as nx
from scipy.stats import chi2_contingency
import pickle

# LOAD DATA
congress_df = pd.read_csv("congress_members.csv")
edgelist = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# No preprocessing is needed, because data is already in the required format.

# ANALYSIS
# Create a pairwise data of `State` and `Party` between nodes in each edge
edges_data = []
for edge in edgelist.edges:
    source_data = congress_df.iloc[int(edge[0])]
    target_data = congress_df.iloc[int(edge[1])]
    edge_data = [source_data.State, target_data.State, source_data.Party, target_data.Party]
    edges_data.append(edge_data)

edges_df = pd.DataFrame(edges_data, columns=['SourceState', 'TargetState', 'SourceParty', 'TargetParty'])

## Table 1: "Chi-square test of party-wise retweet interaction"
# Party-wise retweet interaction
party_wise_interaction = pd.crosstab(edges_df.SourceParty, edges_df.TargetParty)
party_wise_stat, party_wise_p, party_wise_dof, party_wise_expctd = chi2_contingency(party_wise_interaction)

df1 = pd.DataFrame([{'Statistic': party_wise_stat, 'p-value': party_wise_p, 'DoF': party_wise_dof}],
                   columns=['Statistic', 'p-value', 'DoF'], 
                   index=['Party Interaction Analysis'])
df1.to_pickle('table_1.pkl')


## Table 2: "Chi-square test of state-wise retweet interaction"
# State-wise Twitter interaction
state_wise_interaction = pd.crosstab(edges_df.SourceState, edges_df.TargetState)
state_wise_stat, state_wise_p, state_wise_dof, state_wise_expctd = chi2_contingency(state_wise_interaction)

df2 = pd.DataFrame([{'Statistic': state_wise_stat, 'p-value': state_wise_p, 'DoF': state_wise_dof}],
                   columns=['Statistic', 'p-value', 'DoF'], 
                   index=['State Interaction Analysis'])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of Congress members': len(congress_df), 
 'Total number of edges in the graph': len(edgelist.edges),
 'Total number of nodes in the graph': len(edgelist.nodes),
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
