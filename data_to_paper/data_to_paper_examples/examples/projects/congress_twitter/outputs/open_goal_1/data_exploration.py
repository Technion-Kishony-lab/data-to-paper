
import pandas as pd
import networkx as nx

# Load data
df = pd.read_csv('congress_members.csv')
graph = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# Data Size
with open('data_exploration.txt', 'w') as f:
    f.write("# Data Size\n")
    f.write("Number of Rows in congress_members.csv: " + str(len(df)) + "\n") 
    f.write("Number of Columns in congress_members.csv: " + str(len(df.columns)) + "\n") 
    f.write("Number of Edges in congress_edges.dat: " + str(graph.number_of_edges()) + "\n")
    f.write("Number of Nodes in congress_edges.dat: " + str(graph.number_of_nodes()) + "\n")

    # Summary Statistics
    f.write("\n# Summary Statistics\n")
    desc = df.describe(include='all')
    f.write(str(desc) + "\n")

    # Categorical Variables
    f.write("\n# Categorical Variables\n")
    categorical_columns = df.select_dtypes(include='object').columns.tolist()
    for column in categorical_columns:
        f.write("Most common categories in " + column + " :\n")
        f.write(str(df[column].value_counts().head(5)) + "\n")

    # Missing Values
    f.write("\n# Missing Values\n")
    missing_values = df.isna().sum()
    f.write(str(missing_values) + "\n")
