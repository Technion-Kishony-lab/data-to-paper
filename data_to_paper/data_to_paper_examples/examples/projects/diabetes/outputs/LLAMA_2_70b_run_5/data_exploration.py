

import pandas as pd
import numpy as np
import scipy

# Load the dataset
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Create a new output file
with open("data_exploration.txt", "w") as f:
    # Data Size
    f.write("# Data Size\n")
    f.write(f"{len(df.index)} rows, {len(df.columns)} columns\n")
    
    # Summary Statistics
    f.write("\n# Summary Statistics\n")
    f.write(f"mean(BMI): {np.mean(df['BMI'])}\n")
    f.write(f"stddev(BMI): {np.std(df['BMI'])}\n")
    f.write(f"min(BMI): {np.min(df['BMI'])}\n")
    f.write(f"max(BMI): {np.max(df['BMI'])}\n")
    f.write(f"sum(BMI): {np.sum(df['BMI'])}\n")
    
    # Categorical Variables
    categorical_vars = ["Sex", "Age", "Education", "Income"]
    for var in categorical_vars:
        f.write("\n# Categorical Variables\n")
        f.write(f"{var}: \n")
        unique_values = df[var].unique()
        for i, value in enumerate(unique_values):
            f.write(f"{i+1}. {value}")
            count = df[var].value_counts()[value]
            f.write(f" ({count})")
            f.write("\n")
    
    # Missing Values
    missing_values = df.isnull().sum()
    f.write("\n# Missing Values\n")
    f.write(f"{missing_values} rows with missing values out of {len(df)} ({round(100*missing_values/len(df), 2)}%)\n")
    
    # Other summary
    f.write("\n# Other Summary\n")
    f.write(f"Number of non-empty rows: {len(df.dropna())}\n")
    f.write(f"Number of empty rows: {len(df.fillna(0))}\n")  # changed fillna() method to fillna(0) to avoid ValueError
    f.write(f"Unique rows: {len(df.drop_duplicates())} out of {len(df)} ({round(100*len(df.drop_duplicates())/len(df), 2)}%)\n")



