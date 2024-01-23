
import pandas as pd
import numpy as np

# loading data
df = pd.read_csv("tracheal_tube_insertion.csv")

with open('data_exploration.txt', 'w') as f:
    # data size
    f.write("# Data Size\n")
    f.write(f"Number of rows = {df.shape[0]}\n")
    f.write(f"Number of columns = {df.shape[1]}\n\n")

    # summary statistics
    f.write("# Summary Statistics\n")
    desc = df.describe(include="all")
    f.write(desc.to_string())
    f.write("\n\n")

    # categorical variables
    f.write("# Categorical Variables\n")
    categorical_vars = df.select_dtypes(include='object').columns.tolist()
    if categorical_vars:  # if there are any categorical vars
        for var in categorical_vars:
            top_freq = df[var].value_counts().idxmax()
            f.write(f"{var}, most frequent value: {top_freq}\n")
    else:
        f.write("No categorical variables in the dataset.\n")
    f.write("\n")

    # missing values
    f.write("# Missing Values\n")
    missing_counts = df.isnull().sum()
    if missing_counts.any():  # if there are any missing values
        f.write(missing_counts.to_string())
    else:
        f.write("No missing values in the dataset.\n")

    #additional check for special values
    f.write("\nChecking for special numerical values...\n")
    special_counts = (df.select_dtypes(include=['int','float']) == 0).sum()
    if special_counts.any(): 
        f.write(special_counts.to_string())
    else:
        f.write("No special numerical values in the dataset.\n")
