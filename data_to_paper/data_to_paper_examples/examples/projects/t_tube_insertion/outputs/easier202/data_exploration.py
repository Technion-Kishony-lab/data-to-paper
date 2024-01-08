
import pandas as pd
import numpy as np

# Loading the dataset using pandas
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open output file
with open('data_exploration.txt', 'w') as f:

    # Data Size: Number of rows and columns in the dataset
    f.write("# Data Size\n")
    f.write(f"Number of Rows : {df.shape[0]}\n")
    f.write(f"Number of Columns : {df.shape[1]}\n\n")

    # Summary Statistics: Get summary statistics including mean, median, std deviation and quartiles
    f.write("# Summary Statistics\n")
    f.write(df.describe().to_string())
    f.write("\n\n")

    # Categorical Variables: Identify categorical variables and get their most common values
    f.write("# Categorical Variables\n")
    f.write(f"Sex : {df['sex'].value_counts().idxmax()}\n\n")

    # Missing Values: Check and count the number of missing, unknown, or undefined values
    f.write("# Missing Values\n")
    f.write(df.isna().sum().to_string())
    f.write("\n\n")

    # Check for special numeric values that stand for unknown/undefined
    f.write("# Special Numeric Values\n")
    special_values = df.isin([np.nan, np.inf, -np.inf]).sum()
    f.write(special_values.to_string())
    f.write("\n")
