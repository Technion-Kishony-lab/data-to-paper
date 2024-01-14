
# import required packages
import pandas as pd
import numpy as np

# load the data
df = pd.read_csv("tracheal_tube_insertion.csv")

# open our output file
with open("data_exploration.txt", "w") as file:
    
    # write data size
    file.write("# Data Size\n")
    file.write(f"Number of rows: {df.shape[0]}\n")
    file.write(f"Number of columns: {df.shape[1]}\n\n")
    
    # write summary statistics
    file.write("# Summary Statistics\n")
    summary_stats = df.describe(include='all').transpose()
    file.write(f"{summary_stats}\n\n")

    # writing categorical variables
    file.write("# Categorical Variables\n")
    categorical_variables = df.select_dtypes(include='object').nunique()
    for var, unique_counts in categorical_variables.items():
        file.write(f"{var}: {unique_counts} unique values\n")
    file.write("\n")

    # write missing values
    file.write("# Missing Values\n")
    missing_values = df.isnull().sum()
    for var, missing_count in missing_values.items():
        if missing_count > 0:
            file.write(f"{var}: {missing_count} missing values\n")
            
    # Check for special numeric values that stand for unknown/undefined
    nan_cols = df.isna().any()
    file.write("\nColumns with NaN values\n")
    file.write(f"{nan_cols}\n")
