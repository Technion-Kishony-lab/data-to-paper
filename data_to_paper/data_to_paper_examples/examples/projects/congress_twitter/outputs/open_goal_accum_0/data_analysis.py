
# IMPORT
import pandas as pd
import networkx as nx
import pickle
from scipy.stats import chi2_contingency

# LOAD DATA
df_members = pd.read_csv('congress_members.csv')
G = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype=int)

# DATASET PREPARATIONS
# Convert the edges to pandas DataFrame denoting source and target nodes
df_edges = pd.DataFrame(list(G.edges()), columns=['Source_Node', 'Target_Node'])

# Create new series with int type for merging operation
df_edges['Source_Node_int'] = df_edges['Source_Node'].astype(int)
df_edges['Target_Node_int'] = df_edges['Target_Node'].astype(int)

# Merge df_edges with df_members to get additional details for Source_Node and Target_Node chambers
df_edges = df_edges.merge(df_members[['Chamber']], left_on='Source_Node_int', right_index=True)
df_edges.rename(columns={'Chamber': 'Chamber_Source'}, inplace=True)
df_edges = df_edges.merge(df_members[['Chamber']], left_on='Target_Node_int', right_index=True)
df_edges.rename(columns={'Chamber': 'Chamber_Target'}, inplace=True)

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed

# PREPROCESSING
# No preprocessing is needed, as the data are already suitable for our analysis

# ANALYSIS
## Table 1: "Distribution of interactions among House and Senate Members"
# Create a dataframe for Table 1
df1 = pd.crosstab(df_edges['Chamber_Source'], df_edges['Chamber_Target'])
df1.to_pickle('table_1.pkl')

# Calculate chi-square test of independence
chi2, p, dof, expected = chi2_contingency(df1)

## Table 2: "Chi-Square Test of Independence Result"
# Create a dataframe for Table 2
indexData = ['Chi-square Test']
df2_data = [{'Chi-square statistic': chi2, 'p-value': p}]
df2 = pd.DataFrame(df2_data, index=indexData)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df_edges),
 'Chi-square Test Results': {'Chi-square statistic': chi2, 'p-value': p}
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
