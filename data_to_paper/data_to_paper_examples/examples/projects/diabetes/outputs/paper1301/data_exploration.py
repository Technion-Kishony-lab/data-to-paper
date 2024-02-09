
import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Open the output file
with open("data_exploration.txt", "w") as out_file:
    
    # Data Size
    out_file.write("# Data Size\n")
    out_file.write(f"Number of Rows: {df.shape[0]}\n")
    out_file.write(f"Number of Columns: {df.shape[1]}\n")
    out_file.write("\n")
    
    # Summary Statistics
    out_file.write("# Summary Statistics\n")
    summary_stats = df.describe().transpose()
    summary_stats.to_string(out_file)
    out_file.write("\n")
    
    # Categorical Variables
    out_file.write("# Categorical Variables\n")
    categorical_vars = df.select_dtypes(include=['object']).columns
    for var in categorical_vars:
        out_file.write(f"\nFor variable {var}, the top 5 most common values are:\n")
        freq = df[var].value_counts().head(5).to_string()
        out_file.write(f"{freq}\n")
    out_file.write("\n")
    
    # Missing Values
    out_file.write("# Missing Values\n")
    missing_values = df.isnull().sum()
    missing_percentage = missing_values / df.shape[0] * 100
    out_file.write("Number and Percentage of Missing Values for Each Variable are as follows:\n")
    for (col, missing), percentage in zip(missing_values.items(), missing_percentage):
        out_file.write(f"{col}: Count = {missing}, Percentage = {percentage}%\n")
    out_file.write("\n")
    
    # Balance of Target Variable (Diabetes_binary)
    out_file.write("# Balance of Target Variable (Diabetes_binary)\n")
    target_balance = df['Diabetes_binary'].value_counts()
    target_percent = df['Diabetes_binary'].value_counts(normalize=True) * 100
    out_file.write("Count and Percentage for Each Class of Target Variable are as follows:\n")
    for (val, balance), percent in zip(target_balance.items(), target_percent):
        out_file.write(f"Class {val}: Count = {balance}, Percentage = {percent}%\n")

# Close the output file
out_file.close()
