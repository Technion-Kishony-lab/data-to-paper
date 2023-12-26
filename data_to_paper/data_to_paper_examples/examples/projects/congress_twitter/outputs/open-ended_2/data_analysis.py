
# IMPORT
import pandas as pd
import networkx as nx
from scipy import stats
import pickle

# LOAD DATA
members = pd.read_csv('congress_members.csv')
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# Creating numeric IDs for members; adding this column to members dataframe.
members['ID'] = range(len(members))

# ANALYSIS
## Table 1: "Test of Association between Chamber and Density of Out-Edges"
# Create an out-degree centrality measure for each node (member of congress)
out_degrees = pd.DataFrame.from_dict(nx.out_degree_centrality(edges), orient='index', columns=['Out-degree Centrality'])

# Label node IDs and merge with members dataframe
out_degrees['ID'] = out_degrees.index.map(int)
result_table_1 = members.merge(out_degrees, on='ID')

house_out_degrees = result_table_1[result_table_1['Chamber'] == 'House']['Out-degree Centrality']
senate_out_degrees = result_table_1[result_table_1['Chamber'] == 'Senate']['Out-degree Centrality']

f_stat, p_val = stats.f_oneway(house_out_degrees, senate_out_degrees)
df1 = pd.DataFrame({'F Stat': [f_stat], 'p-value': [p_val]}, index=['Chamber'])
df1.to_pickle('table_1.pkl')

## Table 2: "Degree Centrality by Party"
# State level centrality measure
degree_centrality = pd.DataFrame.from_dict(nx.degree_centrality(edges), orient='index', columns=['Degree Centrality'])
degree_centrality['ID'] = degree_centrality.index.map(int)
result_table_2 = members.merge(degree_centrality, on='ID')

by_party = result_table_2.groupby('Party')['Degree Centrality'].mean()
df2 = pd.DataFrame(by_party).rename(columns={'Degree Centrality': 'Average Degree Centrality'})
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = { 
  'Number of Nodes': edges.number_of_nodes(), 
  'Number of Edges': edges.number_of_edges(), 
  'Density of Network': nx.density(edges)
} 

with open('additional_results.pkl', 'wb') as file:
    pickle.dump(additional_results, file)
