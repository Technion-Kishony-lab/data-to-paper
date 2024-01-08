
import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv("tracheal_tube_insertion.csv")

# Open output file
with open("data_exploration.txt", "w") as f:

    # Data Size
    f.write("# Data Size\n")
    f.write("Number of Rows: " + str(df.shape[0]) + "\n")
    f.write("Number of Columns: " + str(df.shape[1]) + "\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    summary_stats = df.describe(include='all')
    summary_stats.to_string(f)
    f.write("\n")

    # Categorical Variables
    f.write("# Categorical Variables\n")
    categorical = df.select_dtypes(include=['object'])
    for name in categorical.columns:
        top_5 = categorical[name].describe().top
        f.write("Most common " + name + " : " + str(top_5) + "\n")
    f.write("\n")

    # Missing Values
    f.write("# Missing Values\n")
    missing_data = df.isnull().sum()
    missing_data.to_string(f)
    f.write("\n")

    # Check for special numeric values that stand for unknown/undefined 
    f.write("# Special Numeric Values\n")
    special_values = df[df.select_dtypes(include=[np.number]) < 0].count()
    special_values.to_string(f)
