
import pandas as pd
import networkx as nx

# Load congress members data from csv file 
df_congress_members = pd.read_csv('congress_members.csv')

# Load congress edges data
G = nx.read_edgelist('congress_edges.dat', create_using=nx.DiGraph())

# Open output file
with open("data_exploration.txt", "w") as file:

    # Data size
    file.write("# Data Size\n")
    file.write(f"Number of Congress members: {df_congress_members.shape[0]}\n")
    file.write(f"Number of attributes per member: {df_congress_members.shape[1]}\n")
    file.write(f"Number of nodes in the graph: {G.number_of_nodes()}\n")
    file.write(f"Number of edges in the graph: {G.number_of_edges()}\n\n")
    
    # Summary statistics
    file.write("# Summary Statistics\n")
    # As there are no continuous variables in this dataset, we will skip this section
    file.write("N/A for this dataset\n\n")

    # Categorical variables
    file.write("# Categorical Variables\n")
    categorical_cols = ['State','Party','Chamber']
    for col in categorical_cols:
        # Count of members per categorical variable
        file.write(f"Count of members per {col}: \n{df_congress_members[col].value_counts()}\n")
        # Most common category for each categorical variable
        top_5 = df_congress_members[col].value_counts().idxmax()
        file.write(f"Most common {col}: {top_5}\n\n")

    # Missing values
    file.write("# Missing Values\n")
    file.write(f"Missing values in each column:\n{df_congress_members.isna().sum()}\n")
    
file.close()
