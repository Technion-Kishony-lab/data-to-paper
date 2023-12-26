
import pandas as pd
import networkx as nx

# Load data
members = pd.read_csv('congress_members.csv')
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# calculate basic statistics
members_count = len(members)
edges_count = edges.number_of_edges()
handle_summary = members['Handle'].describe()
state_summary = members['State'].describe()
party_summary = members['Party'].describe()
chamber_summary = members['Chamber'].describe()
missing_values = members.isnull().sum()

# write to file
with open('data_exploration.txt', 'w') as the_file:
    the_file.write('# Data Size\n')
    the_file.write(f'Members: {members_count}\n')
    the_file.write(f'Edges: {edges_count}\n')

    the_file.write('\n# Summary Statistics\n')
    the_file.write('\n## Handle\n')
    the_file.write(str(handle_summary))
    the_file.write('\n## State\n')
    the_file.write(str(state_summary))
    the_file.write('\n## Party\n')
    the_file.write(str(party_summary))
    the_file.write('\n## Chamber\n')
    the_file.write(str(chamber_summary))

    the_file.write('\n\n# Categorical Variables\n')
    the_file.write(f'State: {members["State"].unique()}\n')
    the_file.write(f'Party: {members["Party"].unique()}\n')
    the_file.write(f'Chamber: {members["Chamber"].unique()}\n')

    the_file.write('\n# Missing Values\n')
    the_file.write(str(missing_values))
