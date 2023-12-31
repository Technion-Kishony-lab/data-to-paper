
# IMPORT
import pandas as pd 
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
import networkx as nx
import pickle
import warnings

# LOAD DATA
df_members = pd.read_csv('congress_members.csv')
graph_edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# DATASET PREPARATIONS
df_members.index = df_members.index.astype(int)
graph_edges = nx.relabel.convert_node_labels_to_integers(graph_edges)

# DESCRIPTIVE STATISTICS
# No descriptive statistics are needed.

# PREPROCESSING
mapping_party = df_members['Party'].to_dict()
mapping_state = df_members['State'].to_dict()
mapping_chamber = df_members['Chamber'].to_dict()
nx.set_node_attributes(graph_edges, mapping_party, 'Party')
nx.set_node_attributes(graph_edges, mapping_state, 'State')
nx.set_node_attributes(graph_edges, mapping_chamber, 'Chamber')

# ANALYSIS
## Table 1: "Chi-Square Test of association between political party and Twitter interactions, accounting for chamber"
df1 = pd.DataFrame(dict(graph_edges.nodes(data=True))).transpose()
degree_values = [graph_edges.degree(n) for n in graph_edges.nodes()]
df1['Degree'] = degree_values
df1 = df1[['Party', 'Chamber', 'Degree', 'State']]

observed = df1.groupby(['Party', 'Chamber'])['Chamber'].count().unstack()
observed = observed.fillna(0) 
row_totals = observed.sum(axis=1)
col_totals = observed.sum(axis=0)
total = observed.sum().sum()
expected = pd.DataFrame(np.outer(row_totals, col_totals) / total, 
                        columns=observed.columns, 
                        index=observed.index)
chi_sq_statistic, p_value, _, _ = stats.chi2_contingency(observed)
table1 = pd.DataFrame({
                           'Observed': observed.sum(axis=1),
                           'Expected': expected.sum(axis=1),
                           'Chi-Sq statistic': [chi_sq_statistic]*observed.shape[0],
                           'P-value': [p_value]*observed.shape[0]
                       })
table1.to_pickle('table_1.pkl')

## Table 2: "ANOVA Test of association between represented state and number of Twitter interactions, accounting for chamber"
model = ols('Degree ~ C(State)', data=df1).fit()
table2 = sm.stats.anova_lm(model, typ=2)
table2 = table2.fillna('-') #replace NaN with '-'
#suppress the warning we know it is OK to ignore
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    table2.loc['Residual', 'PR(>F)'] = "-" # update statistics safely
table2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {'Total number of observations': len(df_members)}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
