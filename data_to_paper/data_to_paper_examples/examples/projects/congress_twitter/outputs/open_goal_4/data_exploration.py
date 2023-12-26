
import pandas as pd
import numpy as np
import networkx as nx

# Load Data
df_members = pd.read_csv('congress_members.csv')
df_edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype=int)

# Initialize file where outputs will be written
file_output = open("data_exploration.txt", 'w')

# Data Size
file_output.write('# Data Size\n')
file_output.write(f'Number of node (congress members): {df_members.shape[0]}\n')
file_output.write(f'Number of attributes for each node: {df_members.shape[1]}\n')
file_output.write(f'Number of edges (interactions): {df_edges.number_of_edges()}\n')

# Summary Statistics
file_output.write('# Summary Statistics\n')
party_counts = df_members['Party'].value_counts()
file_output.write(f'Most common party: {party_counts.idxmax()} with {party_counts.max()} members\n')
chamber_counts = df_members['Chamber'].value_counts()
file_output.write(f'Most common chamber: {chamber_counts.idxmax()} with {chamber_counts.max()} members\n')

# Categorical Variables
file_output.write('# Categorical Variables\n')
file_output.write(f'Values for Party attribute: {df_members["Party"].unique()}\n')
file_output.write(f'Values for Chamber attribute: {df_members["Chamber"].unique()}\n')

# Missing Values
file_output.write('# Missing Values\n')
file_output.write(f'Number of missing or undefined values per attribute:\n {df_members.isnull().sum()}\n')

file_output.close()
