
import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv("tracheal_tube_insertion.csv")

# Writing all the summaries to a text file
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write("# Data Size\n")
    f.write("Number of rows: " + str(df.shape[0]) + "\n")
    f.write("Number of columns: " + str(df.shape[1]) + "\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    summary_stats = df.describe(include=[np.number])
    f.write(str(summary_stats) + "\n\n")

    # Categorical Variables
    f.write("# Categorical Variables\n")
    categorical_vars = df.select_dtypes(include=['object'])
    for column in categorical_vars:
        f.write(str(df[column].value_counts().head()) + "\n\n")

    # Missing Values
    f.write("# Missing Values\n")
    missing_values = df.isnull().sum()
    f.write(str(missing_values[missing_values > 0]) + "\n\n")

    # Check if there is any special numeric value that might stand for unknown/undefined
    f.write("# Investigation for Special Numeric Values\n")
    special_values = df[df < 0].count()
    f.write(str(special_values[special_values > 0]) + "\n") # Assuming negative values are not expected
