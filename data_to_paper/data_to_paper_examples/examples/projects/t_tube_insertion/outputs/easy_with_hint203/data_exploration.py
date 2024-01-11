
import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv("tracheal_tube_insertion.csv")

with open("data_exploration.txt", "w") as file:
    
    # Data Size
    file.write("# Data Size\n")
    file.write(f'Number of Rows: {df.shape[0]}\n')
    file.write(f'Number of Columns: {df.shape[1]}\n\n')

    # Summary Statistics
    file.write("# Summary Statistics\n")
    file.write(df.describe(include='all').to_string())
    file.write("\n\n")

    # Categorical Variables
    file.write("# Categorical Variables\n")
    file.write(f'Most common values for Sex: \n{df["sex"].mode().values}\n\n')

    # Missing Values
    file.write("# Missing Values\n")
    file.write(f'Missing Values: \n{df.isnull().sum().to_string()}\n\n')

    # Zero Values
    file.write("# Zero Values\n")
    file.write(f'Zero values per column: \n{(df == 0).sum(axis=0).to_string()}\n\n')
