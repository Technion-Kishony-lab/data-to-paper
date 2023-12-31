
# IMPORT
import pandas as pd
import networkx as nx
import numpy as np
from statsmodels.formula.api import ols
import pickle

# LOAD DATA
df_members = pd.read_csv('congress_members.csv')
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype=int)

# DATASET PREPARATIONS
state_counts = df_members['State'].value_counts()
df_members['state_rep_count'] = df_members['State'].map(state_counts)

# Use the node of the edge as the index to match with the Congress member DataFrame
in_degree = dict(edges.in_degree())
out_degree = dict(edges.out_degree())
df_members['in_interactions'] = df_members.index.to_series().map(in_degree)
df_members['out_interactions'] = df_members.index.to_series().map(out_degree)

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
df_members = pd.get_dummies(df_members, columns=['Party', 'Chamber'], drop_first=True)

# ANALYSIS
formula1 = 'in_interactions ~ state_rep_count + Party_R + Chamber_Senate'
model1 = ols(formula1, data=df_members.fillna(0)).fit()
df1 = pd.DataFrame({'Beta': model1.params, 'p-value': model1.pvalues})
df1.to_pickle('table_1.pkl')

# New table based on 'out_interactions'
formula2 = 'out_interactions ~ state_rep_count + Party_R + Chamber_Senate'
model2 = ols(formula2, data=df_members.fillna(0)).fit()
df2 = pd.DataFrame({'Beta': model2.params, 'p-value': model2.pvalues})
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df_members),
 'R-squared of regression model (in_interactions)': model1.rsquared, 
 'R-squared of regression model (out_interactions)': model2.rsquared 
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
