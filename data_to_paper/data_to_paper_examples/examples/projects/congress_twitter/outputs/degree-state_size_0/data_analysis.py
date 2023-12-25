
# IMPORT
import pandas as pd
import networkx as nx
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
members_df = pd.read_csv('congress_members.csv')
edges_df = pd.read_csv('congress_edges.dat', sep='\s+', names=['source', 'target'])

# DATASET PREPARATIONS

# Add a 'size' column representing the size of their state 
members_df['Size'] = members_df.groupby('State')['State'].transform('count')

# Create a graph from the edges data
G = nx.from_pandas_edgelist(edges_df, 'source', 'target', create_using=nx.DiGraph())

# Add in-degree and out-degree columns to the members dataframe
members_df['InDegree'] = [G.in_degree(node) for node in range(len(members_df))]
members_df['OutDegree'] = [G.out_degree(node) for node in range(len(members_df))]

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of Size, InDegree, and OutDegree stratified by Party and Chamber"
df0 = members_df.groupby(['Party', 'Chamber'])[['Size', 'InDegree', 'OutDegree']].mean()
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing needed, 'ols' function in statsmodels handles categorical variables.

# ANALYSIS
## Table 1: "Multiple linear regression analysis of in-degree and out-degree as dependent variables, State size as the independent variable, and adjusting for Party and Chamber"

formula_in = 'InDegree ~ Size + C(Party) + C(Chamber)'
formula_out = 'OutDegree ~ Size + C(Party) + C(Chamber)'

model_in = smf.ols(formula=formula_in, data=members_df).fit()
model_out = smf.ols(formula=formula_out, data=members_df).fit()

df1 = pd.DataFrame({'coef_in_degree': model_in.params, 
                    'pvalue_in_degree': model_in.pvalues,
                    'coef_out_degree': model_out.params, 
                    'pvalue_out_degree': model_out.pvalues})

df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(members_df),
 'R-squared of in-degree model': model_in.rsquared,
 'R-squared of out-degree model': model_out.rsquared
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

