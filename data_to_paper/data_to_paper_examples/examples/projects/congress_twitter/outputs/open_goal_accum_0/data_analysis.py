
# IMPORT
import pandas as pd
import numpy as np
import networkx as nx
from statsmodels.formula.api import logit, poisson
import pickle

# LOAD DATA
df_members = pd.read_csv('congress_members.csv')
df_edges = pd.read_csv('congress_edges.dat', sep=" ", header=None, names=['nodeFrom', 'nodeTo'])

# DATASET PREPARATIONS
# Encoding categorical variables
df_members['State_codes'] = df_members['State'].astype('category').cat.codes
df_members['Party_codes'] = df_members['Party'].astype('category').cat.codes
df_members['Chamber_codes'] = df_members['Chamber'].astype('category').cat.codes

# Joining Members and Edges DataFrames
df_edges = df_edges.merge(df_members, left_on='nodeFrom', right_index=True, how='left', suffixes=('_from', '_to'))
df_edges = df_edges.merge(df_members, left_on='nodeTo', right_index=True, how='left', suffixes=('_from', '_to'))

# Creating Binary Variables for Same State and Same Chamber Interactions
df_edges['same_state'] = (df_edges['State_from'] == df_edges['State_to']).astype(int)
df_edges['same_chamber'] = (df_edges['Chamber_from'] == df_edges['Chamber_to']).astype(int)

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# No preprocessing is needed, because the data is already in a form that can be used for analysis.

# ANALYSIS
## Table 1: "Test of association between state representation and interaction on Twitter"
model_1 = logit("same_state ~ State_codes_from + State_codes_to", data=df_edges).fit()
df1 = model_1.summary2().tables[1]
df1.to_pickle("table_1.pkl")

## Table 2: "Test of association between legislative chamber and frequency of Twitter interactions"
df_chamber_interactions = df_edges.groupby(['nodeFrom', 'same_chamber']).size().reset_index(name='interaction_count')
model_2 = poisson("interaction_count ~ same_chamber + nodeFrom", data=df_chamber_interactions).fit()
df2 = model_2.summary2().tables[1]
df2.to_pickle("table_2.pkl")

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df_edges.shape[0],         
    'Number of members': df_members.shape[0],
    'Number of interactions': df_edges.shape[0]
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
