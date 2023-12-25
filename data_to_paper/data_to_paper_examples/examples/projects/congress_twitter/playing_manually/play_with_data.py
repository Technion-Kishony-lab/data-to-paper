import networkx as nx
import pandas as pd
import numpy as np
from statsmodels.formula.api import ols, logit

# read directed graph from file:
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph)
members = pd.read_csv('congress_members.csv')
num_members = len(members)

state_size = members['State'].value_counts()
members['StateSize'] = members['State'].apply(lambda x: state_size[x])

# regression model for eigenvector centrality:
centrality = nx.eigenvector_centrality(edges)
members['EigenvectorCentrality'] = members.index.map({int(k): v for k, v in centrality.items()})
in_degree = nx.in_degree_centrality(edges)
members['InDegree'] = members.index.map({int(k): v for k, v in in_degree.items()})
out_degree = nx.out_degree_centrality(edges)
members['OutDegree'] = members.index.map({int(k): v for k, v in out_degree.items()})

# exclude within state edges for in-degree:
edges_excluding_within_state = edges.copy()
for edge in edges.edges():
    if members.loc[int(edge[0]), 'State'] == members.loc[int(edge[1]), 'State']:
        edges_excluding_within_state.remove_edge(*edge)
in_degree_excluding_within_state = nx.in_degree_centrality(edges_excluding_within_state)
members['InDegreeExcludingWithinState'] = members.index.map({int(k): v for k, v in in_degree_excluding_within_state.items()})
out_degree_excluding_within_state = nx.out_degree_centrality(edges_excluding_within_state)
members['OutDegreeExcludingWithinState'] = members.index.map({int(k): v for k, v in out_degree_excluding_within_state.items()})

model = ols("StateSize ~ C(Party) + C(Chamber) + InDegree + OutDegree", data=members).fit()
print(model.summary(), '\n\n')

model = ols("StateSize ~ C(Party) + C(Chamber) + InDegreeExcludingWithinState + OutDegreeExcludingWithinState", data=members).fit()
print(model.summary(), '\n\n')



# MATRIX MODEL:
state1 = members['State'].values.reshape(-1, 1)
state2 = state1.T
party1 = members['Party'].values.reshape(-1, 1)
party2 = party1.T
chamber1 = members['Chamber'].values.reshape(-1, 1)
chamber2 = chamber1.T
state_size1 = members['StateSize'].values.reshape(-1, 1)
state_size2 = state_size1.T

same_party = party1 == party2
same_chamber = chamber1 == chamber2
same_state = state1 == state2

state_size1_mat = np.repeat(state_size1, num_members, axis=1)
state_size2_mat = np.repeat(state_size2, num_members, axis=0)


connectivity_matrix = nx.to_numpy_array(edges)

# regression model for the probability of a link:

df = pd.DataFrame({
    'Y': connectivity_matrix.flatten(),
    'SameParty': same_party.flatten(),
    'SameChamber': same_chamber.flatten(),
    'SameState': same_state.flatten(),
    'StateSize1': state_size1_mat.flatten(),
    'StateSize2': state_size2_mat.flatten(),
})

table1_model = logit("Y ~ SameParty + SameChamber + SameState + StateSize1 + StateSize2", data=df).fit()
print(table1_model.summary())

