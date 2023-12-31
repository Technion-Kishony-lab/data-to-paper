
import pandas as pd
import numpy as np
import networkx as nx

# load data
members = pd.read_csv('congress_members.csv')
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# open the output file
with open('data_exploration.txt', 'w') as f:

    ########## DATA SIZE #############
    f.write('# Data Size\n')
    f.write(f'Number of nodes (Congress members): {len(members)}\n')
    f.write(f'Number of edges (Interactions): {edges.number_of_edges()}\n')
    f.write('\n')

    ########## SUMMARY STATISTICS #############
    f.write('# Summary Statistics\n')
    f.write('## Members file:\n')
    f.write(members.describe(include='all').to_string())
    f.write('\n')
    f.write('## Edges file:\n')
    f.write(f'Number of interactions per node:\n')
    f.write(pd.Series([d for n, d in edges.degree()], name='Degree').describe().to_string())
    f.write('\n\n')

    ########## CATEGORICAL VARIABLES #############
    f.write('# Categorical Variables\n')
    f.write('## Members file:\n')
    for col in ['State', 'Party', 'Chamber']:
        f.write(f'{col} most common values:\n')
        f.write(members[col].value_counts().head().to_string())
        f.write('\n')
    f.write('\n')
    
    ########## MISSING VALUES #############
    f.write('# Missing Values\n')
    f.write('## Members file:\n')
    f.write(members.isna().sum().to_string())  
    f.write('\n\n')

