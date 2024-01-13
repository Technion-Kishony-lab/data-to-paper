
import pandas as pd
import numpy as np

# Load the data
data = pd.read_csv("tracheal_tube_insertion.csv")

# Create an output file
with open("data_exploration.txt", "w") as out:

    # Data Size
    out.write("# Data Size\n")
    out.write(f"Number of Rows: {data.shape[0]}\n")
    out.write(f"Number of Columns: {data.shape[1]}\n\n")
    
    # Summary Statistics
    out.write("# Summary Statistics\n")
    summary_stats = data.describe()
    out.write(str(summary_stats))
    out.write("\n\n")

    # Categorical Variables
    out.write("# Categorical Variables\n")
    categorical_variables = data.select_dtypes(include=['object'])
    for name in categorical_variables:
        out.write(f"{name}: \n")
        out.write(str(data[name].value_counts().head()))
    out.write("\n\n")

    # Missing Values
    out.write("# Missing Values\n")
    missing_values = data.isnull().sum()
    out.write(str(missing_values))
    
    # Check for special numeric values
    out.write("\n\n")
    out.write("# Special Numerical Values\n")
    for col in data.columns:
        special_count = data[data[col] < 0].count()[col]
        out.write(f"{col}: {special_count} special numerical values\n")

    # Other summaries if you deem necessary
    out.write("\n\n")
    
    out.close()
