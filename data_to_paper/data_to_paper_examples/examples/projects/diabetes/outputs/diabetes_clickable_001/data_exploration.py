
import pandas as pd
import numpy as np

# Read in the CSV data
data = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Open output file
with open("data_exploration.txt", "w") as file:

    # Data Size
    file.write("# Data Size\n")
    file.write(f"Number of Rows: {data.shape[0]}\n")
    file.write(f"Number of Columns: {data.shape[1]}\n\n")
    
    # Summary Statistics
    file.write("# Summary Statistics\n")
    summary_stats = data.describe(include=np.number).transpose()
    summary_stats.to_csv(file, sep="\t")
    file.write("\n")
    
    # Categorical Variables
    categorical_columns = data.select_dtypes(include=['object']).columns
    file.write("# Categorical Variables\n")
    if len(categorical_columns) == 0:
        file.write("Not Applicable\n\n")
    else:
        for col in categorical_columns:
            file.write(f"For variable: {col}\n")
            file.write(f"Mode: {data[col].mode()[0]}\n")
        file.write("\n")

    # Missing Values
    file.write("# Missing Values\n")
    total_missing = data.isnull().sum().sum()
    if total_missing == 0:
        file.write("No missing values\n\n")
    else:
        file.write(f"Total missing values: {total_missing}\n")
        missing_values = data.isnull().sum()
        missing_values.to_csv(file, sep="\t")
        file.write("\n")
