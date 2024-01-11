
import pandas as pd
import numpy as np

# Load the data into a pandas DataFrame
df = pd.read_csv("tracheal_tube_insertion.csv")

# Open an output file to write results
with open("data_exploration.txt", "w") as output_file:

    # Data size
    output_file.write("# Data Size\n")
    output_file.write(f"Number of rows: {df.shape[0]}\n")
    output_file.write(f"Number of columns: {df.shape[1]}\n\n")
    
    # Summary Statistics
    output_file.write("# Summary Statistics\n")
    summary_stats = df.describe(include="all") # summary stats for all variables
    output_file.write(f"{summary_stats}\n\n")
    
    # Categorical Variables
    output_file.write("# Categorical Variables\n")
    categorical_vars = df.select_dtypes(include=["object", "bool"]).columns # Get categorical variables
    for var in categorical_vars:
        output_file.write(f"Variable '{var}' most common values:\n")
        output_file.write(f"{df[var].value_counts().head()}\n")
    if len(categorical_vars) == 0:
        output_file.write("There are no categorical variables in the dataset.\n")
    output_file.write("\n")

    # Missing Values
    output_file.write("# Missing Values\n")
    missing_values = df.isnull().sum() # Get missing values
    output_file.write(f"{missing_values}\n")
    if missing_values.sum() == 0:
        output_file.write("There are no missing values in the dataset.\n")
    output_file.write("\n")

    # Check if the numeric columns contain any special values that mean unknown/undefined
    output_file.write("# Special numeric values (unknown/undefined)\n")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist() # list of all numeric columns
    check_cols = ['tube', 'age_c', 'ht', 'wt', 'tube_depth_G'] # list of numeric columns to check for special values
    special_values = [col for col in check_cols if col in numeric_cols]
    if len(special_values) == 0:
        output_file.write("There are no special numeric values that mean unknown or undefined in the dataset.\n")
    else: 
        for col in special_values:
            special_val_counts = df.loc[df[col] < 0, col].count() # assuming that negative values are special values
            output_file.write(f"{col}: {special_val_counts}\n")

