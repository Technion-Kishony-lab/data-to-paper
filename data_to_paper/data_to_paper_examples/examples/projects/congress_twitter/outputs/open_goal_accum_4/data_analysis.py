
# IMPORT
import pandas as pd
import networkx as nx
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())
members = pd.read_csv('congress_members.csv')

# DATASET PREPARATIONS
# create a column indicating the engagement count (number of Twitter interactions) for each congress member
engagement_dict = {int(n): degree for n, degree in edges.out_degree()}
members["EngagementCount"] = members.index.map(engagement_dict).fillna(0)

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# Create a new column indicating the size of representation for each congress member's state
state_counts = members['State'].value_counts()
members['StateRepresentation'] = members['State'].apply(lambda x: state_counts[x])

# Drop any NaN rows resulted from previous operations
members.dropna(inplace=True)

# ANALYSIS
## Table 1: "Mean and standard deviation of Twitter interactions of Congress members by Party and Chamber"
df1 = members.groupby(['Party', 'Chamber']).EngagementCount.agg(['mean', 'std'])
df1.to_pickle('table_1.pkl')

## Table 2: "ANOVA results for the effect of state representation size on Twitter interactions, controlling for party and chamber"
model = smf.ols('EngagementCount ~ StateRepresentation + C(Party) + C(Chamber)', data=members).fit()

# Extract the p-values, coefficients and confidence intervals from the fitted model
parameters = model.params
pvalues = model.pvalues
conf_ints = model.conf_int()
df2 = pd.concat([parameters, pvalues, conf_ints], axis=1)
df2.columns = ['coef', 'pvalue', 'CI_lower', 'CI_upper']
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(members), 
    'Total number of interactions': members['EngagementCount'].sum(),
    'Model R-squared': model.rsquared
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
