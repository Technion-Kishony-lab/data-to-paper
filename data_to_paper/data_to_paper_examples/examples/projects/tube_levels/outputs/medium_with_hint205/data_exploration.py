
import pandas as pd
import numpy as np

# Loading the data
df = pd.read_csv("tracheal_tube_insertion.csv")

# Creating a summary text file
with open("data_exploration.txt", "w") as f:
    # Data size
    f.write("# Data Size\n")
    f.write(f"Number of rows: {len(df)}\n")
    f.write(f"Number of columns: {len(df.columns)}\n\n")

    # Summary statistics
    f.write("# Summary Statistics\n")
    f.write(df.describe(include='all').to_string())
    f.write("\n\n")

    # Categorical variable(s)
    f.write("# Categorical Variables\n")
    f.write(df['sex'].value_counts().to_string())
    f.write("\n\n")

    # Missing values
    f.write("# Missing Values\n")
    f.write(df.isnull().sum().to_string())
    f.write("\n\n")

    # Checking for special numeric values that stand for unknown/undefined
    f.write("# Special Numeric Values\n")
    special_vals = df.applymap(np.isreal).sum() != len(df)
    f.write(special_vals[special_vals == True].to_string())
    f.write("\n")
