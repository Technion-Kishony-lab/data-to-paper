
# IMPORT
import pandas as pd
import numpy as np
import networkx as nx
import pickle
from sklearn.preprocessing import LabelEncoder
from scipy.stats import chi2_contingency

# LOAD DATA
df_members = pd.read_csv('congress_members.csv')
df_edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# Encoding categorical variables
state_encoder = LabelEncoder()
df_members['State_code'] = state_encoder.fit_transform(df_members['State'])
party_encoder = LabelEncoder()
df_members['Party_code'] = party_encoder.fit_transform(df_members['Party'])
chamber_encoder = LabelEncoder()
df_members['Chamber_code'] = chamber_encoder.fit_transform(df_members['Chamber'])

# ANALYSIS
## Table 1: "Chi-Squared Test of Independence between Represented State and Occurrence of Twitter Interactions"

# Create a contingency table for Twitter Interactions and Represented State
contingency_state_interactions = pd.crosstab(df_members['State_code'], df_edges)

# Perform the Chi-squared test of independence
chi2_stat, p_val, dof, ex = chi2_contingency(contingency_state_interactions)

# Create a dataframe for the table with meaningful row labels
df1 = pd.DataFrame({"Chi-Squared Statistic": [chi2_stat], "p-value": [p_val]}, 
                   index=["Chi-Squared Test: State and Interactions"])
df1.to_pickle('table_1.pkl')

## Table 2: "Chi-Squared Test of Independence between the Member's Chamber and Occurrence of Twitter Interactions"

# Create a contingency table for Twitter Interactions and Chambers
contingency_chamber_interactions = pd.crosstab(df_members['Chamber_code'], df_edges)

# Perform the Chi-squared test of independence
chi2_stat, p_val, dof, ex = chi2_contingency(contingency_chamber_interactions)

# Create a dataframe for the table with meaningful row labels
df2 = pd.DataFrame({"Chi-Squared Statistic": [chi2_stat], "p-value": [p_val]}, 
                   index=["Chi-Squared Test: Chamber and Interactions"])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total Number of Members': df_members.shape[0], 
 'Total Number of Twitter Interactions': df_edges.size()
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
