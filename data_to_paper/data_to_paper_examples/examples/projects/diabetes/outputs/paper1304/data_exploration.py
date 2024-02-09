
import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Open the output file
with open("data_exploration.txt", "w") as f:

    # Data Size
    f.write("# Data Size\n")
    f.write(f"Number of rows: {df.shape[0]}\n")
    f.write(f"Number of columns: {df.shape[1]}\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    desc = df.describe()
    f.write(f"{desc}\n\n")

    # Categorical Variables
    f.write("# Categorical Variables\n")
    categorical_columns = df.select_dtypes(include=['object']).columns
    for cat_col in categorical_columns:
        f.write(f"{cat_col} - most common values:\n")
        f.write(f"{df[cat_col].value_counts().head()}\n\n")
    
    # Missing Values
    f.write("# Missing Values\n")
    missing = df.isnull().sum()
    f.write(f"{missing}\n")
    
    # Look for special numeric values that stand for unknown/undefined
    special_values = df.isin([99, 88, 77]).sum()  #you may adjust these values as needed based on your data set 
    if special_values.sum() > 0:
        f.write("\nCounts of special numeric values (99,88,77) that stand for unknown/undefined:\n")
        f.write(f"{special_values}\n")
