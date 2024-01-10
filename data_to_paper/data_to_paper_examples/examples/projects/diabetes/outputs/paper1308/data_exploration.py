
import pandas as pd
import numpy as np

# Import Data
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Create an output file
with open('data_exploration.txt', 'w') as f:
    
    # Data Size
    f.write("# Data Size\n")
    f.write(f'Rows: {df.shape[0]}, Columns: {df.shape[1]}\n\n')

    # Summary Statistics
    f.write("# Summary Statistics\n")
    stats = df.describe(include='all')
    f.write(stats.to_string())
    f.write('\n\n')
    
    # Categorical Variables
    categorical_variables = df.select_dtypes(include=['int', 'bool'])
    f.write("# Categorical Variables\n")
    for var in categorical_variables:
        f.write(f"`{var}`\n")
        f.write(df[var].value_counts().to_string())
        f.write('\n\n')
    
    #Missing values
    f.write("# Missing Values\n")
    missing = df.isnull().sum()
    f.write(missing.to_string())

f.close()
