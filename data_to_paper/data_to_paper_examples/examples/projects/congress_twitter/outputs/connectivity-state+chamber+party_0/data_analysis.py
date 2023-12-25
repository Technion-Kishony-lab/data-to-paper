
# IMPORT
import pandas as pd
import networkx as nx
import numpy as np
from statsmodels.formula.api import logit
import pickle

# LOAD DATA
members = pd.read_csv('congress_members.csv')
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype=int)

# DATASET PREPARATIONS
# Adding ID column to members data
members['ID'] = np.arange(len(members))

# Create new columns indicating number of represented members by state, party, and chamber
members['state_size'] = members.groupby('State')['ID'].transform('count')

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of state size."
df0 = members[['state_size']].agg(['mean', 'std'])
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed, the data is already cleaned.

# ANALYSIS
# Table 1: "Logistic regression results for the influence of member's state size on the likelihood of interactions."
interaction_table = pd.DataFrame(index=members.index, columns=members.index)
for source, target in edges.edges():
    interaction_table.loc[source, target] = 1
    
interaction_table.fillna(0, inplace=True)
interaction_table = interaction_table.stack().reset_index()
interaction_table.columns = ['source', 'target', 'interaction']
interaction_table['source_state_size'] = interaction_table['source'].map(members['state_size'])
interaction_table['source_party'] = interaction_table['source'].map(members['Party'])
interaction_table['source_chamber'] = interaction_table['source'].map(members['Chamber'])

# Normalize state size
interaction_table['source_state_size_norm'] = (interaction_table['source_state_size'] - interaction_table['source_state_size'].min()) / (interaction_table['source_state_size'].max() - interaction_table['source_state_size'].min())

formula_1 = 'interaction ~ source_state_size_norm + C(source_party) + C(source_chamber) - 1'
model1 = logit(formula_1, interaction_table).fit(disp=0)

df1 = pd.DataFrame()
df1['Stats'] = model1.params.index
df1['Coefficient'] = model1.params.values
df1['P-values'] = model1.pvalues.values
df1 = df1.set_index('Stats')

df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of members': len(members), 
 'Total number of interactions': len(edges.edges())
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
