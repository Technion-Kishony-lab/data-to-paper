
# IMPORT
import pandas as pd
import numpy as np
import networkx as nx
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
members = pd.read_csv("congress_members.csv")
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype = int)

# DATASET PREPARATIONS
node_dict = members.to_dict("index")
interaction_sum = edges.out_degree()
members['Interactions'] = members.index.map(interaction_sum)
members['Interactions'].fillna(0, inplace=True)

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed for this analysis.

# PREPROCESSING
dummies = pd.get_dummies(members[['Party', 'Chamber']], drop_first=True)
members = pd.concat([members, dummies], axis=1)
members['State_Representatives'] = members.groupby('State')['State'].transform('count')

# ANALYSIS
## Table 1: "Analysis of variance for number of interactions grouped by States"
interaction_grouped_by_states = members.groupby("State")["Interactions"].apply(list)
fval, pval = stats.f_oneway(*interaction_grouped_by_states)
table_1 = pd.DataFrame({'F-statistic': [fval], 'p-value': [pval]}, index=['Interactions'])
table_1.index.name = 'Variable'
table_1.to_pickle('table_1.pkl')

## Table 2: "Linear regression analysis of interactions count based on Party, Chamber, and the number of representatives per State"

# Remove interaction term due to multicollinearity
model = smf.ols(formula = "Interactions ~ State_Representatives + C(Party) + C(Chamber)", data = members)
results = model.fit()
conf_int = results.conf_int()
conf_int.columns = ['5%', '95%']
table_2 = pd.concat([results.params, results.pvalues, conf_int], axis=1)
table_2.columns = ['coefficient', 'p-value', '5% confidence interval', '95% confidence interval']
table_2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(members), 
    'Number of interactions': members['Interactions'].sum(),
    'Number of states': members['State'].nunique(),
    'Average interactions per state': members.groupby('State')['Interactions'].mean().mean(),
    'Average interactions per Congress member': members['Interactions'].mean()
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
