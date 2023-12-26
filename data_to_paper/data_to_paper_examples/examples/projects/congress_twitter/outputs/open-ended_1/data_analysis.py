
# IMPORT
import pandas as pd
import networkx as nx
from sklearn.preprocessing import LabelEncoder
import statsmodels.formula.api as smf 
import pickle

# LOAD DATA
members = pd.read_csv('congress_members.csv')
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype = int)

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics are needed.

# PREPROCESSING
# Transform categorical data into binary format
labelencoder = LabelEncoder()
members['Party_Code'] = labelencoder.fit_transform(members['Party'])
members['Chamber_Code'] = labelencoder.fit_transform(members['Chamber'])

# ANALYSIS

## Table 1: "Number of Interactions by Party and Chamber"
# Creating a new dataframe for analysis
edges_df = pd.DataFrame([(edge[0], edge[1]) for edge in edges.edges()], columns=['From', 'To'])
df = edges_df.join(members, on='From').join(members, on='To', lsuffix='_From', rsuffix='_To')
df['Interacted'] = (df.Party_Code_From == df.Party_Code_To) & (df.Chamber_Code_From == df.Chamber_Code_To)
interaction_counts = df.groupby(['Party_From', 'Chamber_From', 'Interacted']).size().reset_index(name='Counts')
df1 = interaction_counts.pivot_table(index=['Party_From', 'Chamber_From'], columns='Interacted', values='Counts').reset_index()
df1['Index'] = df1['Party_From'] + "_" + df1['Chamber_From']
df1.set_index('Index',inplace = True)
df1.fillna('-', inplace=True)
df1.to_pickle('table_1.pkl')

## Table 2: "Logit Regression Results"
# We will create an Interacted_Code column that will be binary (1 if there was an interaction, 0 otherwise)
df['Interacted_Code'] = labelencoder.fit_transform(df['Interacted'])
# Logistic Regression
logit_model = smf.logit(formula='Interacted_Code ~ Party_Code_From + Party_Code_To + Chamber_Code_From + Chamber_Code_To', data=df)
result = logit_model.fit()
summary = result.summary2().tables[1]
summary.reset_index(inplace=True)
summary.columns = ['Variable', 'Coeff.', 'Std.Err.', 'z', 'P>|z|', '[0.025', '0.975]']
df2 = summary.set_index('Variable')
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df), 
 'p-value of logistic regression': result.pvalues[0]
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
