
# Required Libraries
import pandas as pd
import numpy as np

# Load Data
data = pd.read_csv("tracheal_tube_insertion.csv")

# Open the Output File
with open("data_exploration.txt", "w") as file:

    # Data Size
    file.write("# Data Size\n")
    file.write(f"Number of Rows: {data.shape[0]} \n")
    file.write(f"Number of Columns: {data.shape[1]} \n\n")
    
    # Summary Statistics
    file.write("# Summary Statistics\n")
    des = data.describe(include='all')
    des_str = des.to_string()
    file.write(f"{des_str} \n\n")
    
    # Categorical Variables
    file.write("# Categorical Variables\n")
    cat_var = data.select_dtypes(include=['object']).columns
    for var in cat_var:
        value_counts = data[var].value_counts().idxmax()
        file.write(f"For {var}, the most common value is {value_counts}\n")
    if len(cat_var)==0:
        file.write('No categorical variables\n')
    file.write('\n')
    
    # Missing Values
    file.write("# Missing Values\n")
    missing = data.isnull().sum()
    missing_str = missing.to_string()
    file.write(f"{missing_str} \n\n")

    # Special numeric values
    file.write("# Special numeric values\n")
    for col in data.columns:
        if 'undefined' in data[col].tolist() or 'unknown' in data[col].tolist():
            count_undefined = data[col].tolist().count('undefined')
            count_unknown = data[col].tolist().count('unknown')
            file.write(f"For {col}, undefined: {count_undefined}, unknown: {count_unknown} \n")
    file.write("\n")
