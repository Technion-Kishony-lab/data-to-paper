
# IMPORT
import pandas as pd
import networkx as nx
import statsmodels.api as sm
from statsmodels.formula.api import ols
import pickle

# LOAD DATA
members = pd.read_csv("congress_members.csv")
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# DATASET PREPARATIONS
# Add node attributes to the network from the members dataframe
for i, row in members.iterrows():
    edges.nodes[str(i)]['State'] = row['State']
    edges.nodes[str(i)]['Party'] = row['Party']
    edges.nodes[str(i)]['Chamber'] = row['Chamber']

# Get degrees (in, out degree) for each node and add as node attribute
degrees = edges.degree()
in_degrees = edges.in_degree()
out_degrees = edges.out_degree()
for node, degree in degrees:
    edges.nodes[node]['Degree'] = degree
    edges.nodes[node]['InDegree'] = in_degrees[node]
    edges.nodes[node]['OutDegree'] = out_degrees[node]

# Create state size variable and map to nodes
state_sizes = members.groupby('State').size()
for node in edges.nodes():
    edges.nodes[node]['StateSize'] = state_sizes[edges.nodes[node]['State']]

# Convert graph to a pandas dataframe
df = pd.DataFrame.from_dict(dict(edges.nodes(data=True)), orient='index')

# Remove interactions between members from the same state
df = df[df['State'] != df.index]

# DESCRIPTIVE STATISTICS
# Extract only Mean and Standard Deviation for Continuous Variables, Frequency for Categorical Variables
continuous_columns = ['InDegree', 'OutDegree', 'StateSize']
stat_continuous = df[continuous_columns].describe().loc[['mean', 'std']]

categorical_columns = ['Party','Chamber']
frequency_count = df[categorical_columns].describe(include='object').loc[['freq']]

# Merge Statistics for Continuous and Categorical Variables
df0 = pd.concat([stat_continuous, frequency_count], axis=1)
df0 = df0.fillna('-')
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# Get dummies for categorical vars
df = pd.get_dummies(df, columns=['Party', 'Chamber'])

# Create new variables for statsmodels formula
df['Party_D_str'] = df['Party_D'].astype(str)
df['Party_R_str'] = df['Party_R'].astype(str)
df['Party_I_str'] = df['Party_I'].astype(str)
df['Chamber_House_str'] = df['Chamber_House'].astype(str)
df['Chamber_Senate_str'] = df['Chamber_Senate'].astype(str)

# ANALYSIS
## Table 1: "Multiple Linear Regression: Effects of State Size, Party, and Chamber on In-Degree"
# In-degree analysis
model_in = ols("InDegree ~ StateSize + Party_D_str + Party_R_str + Chamber_House_str + Chamber_Senate_str", df).fit()

df1 = pd.DataFrame(model_in.params, columns=['Coefficients'])
df1['Standard Errors'] = model_in.bse
df1['p-value'] = model_in.pvalues
df1.to_pickle('table_1.pkl')

## Table 2: "Multiple Linear Regression: Effects of State Size, Party, and Chamber on Out-Degree"
# Out-degree analysis
model_out = ols("OutDegree ~ StateSize + Party_D_str + Party_R_str + Chamber_House_str + Chamber_Senate_str", df).fit()

df2 = pd.DataFrame(model_out.params, columns=['Coefficients'])
df2['Standard Errors'] = model_out.bse
df2['p-value'] = model_out.pvalues
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0], 
 'r_squared_indegree_model': model_in.rsquared,
 'r_squared_outdegree_model': model_out.rsquared,
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
