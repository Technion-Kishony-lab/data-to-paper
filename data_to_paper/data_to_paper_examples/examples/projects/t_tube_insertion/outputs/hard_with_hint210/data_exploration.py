
import pandas as pd
import numpy as np

# Load CSV data into pandas DataFrame
df = pd.read_csv("tracheal_tube_insertion.csv")

# Open file to write output
with open('data_exploration.txt', 'w') as f:  
   
    # Data Size
    f.write("# Data Size\n")
    f.write(f"Number of Rows, Columns: {df.shape}\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    summary_stats = df.describe(include='all')
    summary_stats_str = summary_stats.to_string() 
    f.write(f"{summary_stats_str}\n\n")
     
    # Categorical Variables
    f.write("# Categorical Variables\n")
    categorical_variables = df.select_dtypes(include=['object']).columns
    if len(categorical_variables) > 0:
        for var in categorical_variables:
            f.write(f"Most common values for variable {var}: {df[var].mode()[0]}\n")
    else:
        f.write("No categorical variables in data.\n")
    f.write("\n")

    # Missing Values
    f.write("# Missing Values\n")
    missing_values = df.isnull().sum()
    missing_values_str = missing_values.to_string() 
    f.write(f"{missing_values_str}\n\n")
    
f.close()
