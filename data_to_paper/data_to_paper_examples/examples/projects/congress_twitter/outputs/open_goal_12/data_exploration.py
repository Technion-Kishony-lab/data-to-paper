
import pandas as pd
import networkx as nx

# read members data
members = pd.read_csv('congress_members.csv')

# read edges data
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# open a new text file and write the analyses
with open('data_exploration.txt', 'w') as outfile:

    # data size
    outfile.write("# Data Size\n")
    outfile.write(f'Number of nodes (Congress members): {len(members)}\n')

    num_edges = edges.number_of_edges()
    outfile.write(f'Number of edges (interactions): {num_edges}\n\n')

    # summary statistics
    outfile.write("# Summary Statistics\n")
    party_counts = members['Party'].value_counts().to_string()
    chamber_counts = members['Chamber'].value_counts().to_string()

    outfile.write(f'Party counts:\n{party_counts}\n')
    outfile.write(f'Chamber counts:\n{chamber_counts}\n\n')

    # categorical variables
    outfile.write("# Categorical Variables\n")
    parties = members['Party'].unique()
    chambers = members['Chamber'].unique()

    outfile.write(f'Unique parties: {", ".join(parties)}\n')
    outfile.write(f'Unique chambers: {", ".join(chambers)}\n\n')

    # missing values
    outfile.write("# Missing Values\n")
    na_counts = members.isna().sum().to_string()

    outfile.write(f'NA counts:\n{na_counts}\n')
