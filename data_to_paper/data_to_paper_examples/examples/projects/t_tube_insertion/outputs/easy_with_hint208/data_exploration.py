
import pandas as pd
import numpy as np

# Reading the data
data = pd.read_csv("tracheal_tube_insertion.csv")

# File where to write the summary
with open("data_exploration.txt", "w") as file:

    # Data Size
    file.write("# Data Size\n")
    file.write(f"Number of rows: {data.shape[0]}\n")
    file.write(f"Number of columns: {data.shape[1]}\n\n")

    # Summary Statistics
    file.write("# Summary Statistics\n")
    desc = data.describe(include='all').transpose()
    file.write(desc.to_string())
    file.write("\n\n")
    
    # Categorical Variables
    file.write("# Categorical Variables\n")
    cat_variables = data.select_dtypes(include=['object']).keys()
    for var in cat_variables:
        file.write(f"{var}\n")
        file.write(f"{data[var].value_counts().head(10)}\n")
    file.write("\n")
     
    # Missing Values
    file.write("# Missing Values\n")
    null_counts = data.isnull().sum()
    file.write(null_counts.to_string())
    file.write("\n\n")
    
    # Special numeric values representing unknown/undefined if any. (assumption none based on the problem statement)
