
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv("tracheal_tube_insertion.csv")

# Open the "data_exploration.txt" file for writing
outfile = open("data_exploration.txt", "w")

# Data Size
outfile.write("# Data Size\n")
rows, cols = df.shape
outfile.write(f'Number of rows: {rows}\n')
outfile.write(f'Number of columns: {cols}\n\n')

# Summary Statistics
outfile.write("# Summary Statistics\n")
summary_stats = df.describe()
outfile.write(str(summary_stats))
outfile.write('\n\n')

# Categorical Variables
outfile.write("# Categorical Variables\n")
categorical_cols = df.select_dtypes(exclude=['int', 'float']).columns
for col in categorical_cols:
    top_value = df[col].value_counts().idxmax()
    outfile.write(f'Most common value of {col}: {top_value}\n')
outfile.write("\n")

# Missing Values
outfile.write("# Missing Values\n")
outfile.write(f'Total missing values: {df.isnull().sum().sum()}\n')
for col in df.columns:
    missing = df[col].isnull().sum()
    if missing > 0:
        outfile.write(f'{col} has {missing} missing values.\n')

# Check/fetch specific numeric values standing for unknown/undefined values, as defined in the dataset description
# For this dataset, there are no such special numeric values substituting unknown/undefined context mentioned in dataset description.

outfile.close()
