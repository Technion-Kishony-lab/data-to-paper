
import pandas as pd
import networkx as nx

# Load data
members = pd.read_csv('congress_members.csv')
edges = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph(), nodetype=int)

# Create file for writing
file = open('data_exploration.txt', 'w')

# Data Size
file.write('# Data Size\n')
file.write('Number of members: ' + str(members.shape[0]) + '\n')
file.write('Number of edges: ' + str(edges.number_of_edges()) + '\n')

# Summary Statistics
file.write('\n# Summary Statistics\n')
file.write(members.describe(include = ['O']).to_string() + '\n')

# Categorical Variables
file.write('\n# Categorical Variables\n')
for column in members.select_dtypes(include='object').columns:
    file.write('Column: ' + column + '\n')
    file.write(str(members[column].value_counts().head())+ '\n')

# Missing Values
file.write('\n# Missing Values\n')
file.write('Missing values in member data: ' + str(members.isnull().sum().sum()) + '\n')

# Close file
file.close()
