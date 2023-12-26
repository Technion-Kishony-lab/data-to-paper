
import pandas as pd
import networkx as nx

df = pd.read_csv("congress_members.csv") # load congress members' data into DataFrame
Graph = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph()) # load edges into NetworkX graph
output_file = open('data_exploration.txt', 'w')

# Compute size of our data
output_file.write('# Data Size\n')
output_file.write(f'Total number of Congress members: {df.shape[0]}\n')
output_file.write(f'Total number of Twitter Interactions: {len(Graph.edges())}\n\n')

# Compute summary statistics
output_file.write('# Summary Statistics\n')
output_file.write(df.describe().to_string())
output_file.write('\n\n')

# List categorical values and their most common values
output_file.write('# Categorical Variables\n')
categorical_columns = df.select_dtypes(['object']).columns
for col in categorical_columns:
    output_file.write(f'Most common value in column "{col}": {df[col].mode().values[0]}\n')
output_file.write('\n')

# Check for missing values
output_file.write('# Missing Values\n')
output_file.write(df.isnull().sum().to_string())
output_file.write('\n')

output_file.close()
