
# Required Libraries
import pandas as pd
import numpy as np

# Load Data
df = pd.read_csv("tracheal_tube_insertion.csv")

# Open File to Write Summary
with open("data_exploration.txt", "w") as file:

    # Data Size
    file.write("# Data Size\n")
    file.write(f"Number of Rows: {df.shape[0]}\n")
    file.write(f"Number of Columns: {df.shape[1]}\n\n")

    # Summary Statistics
    file.write("# Summary Statistics\n")
    summary_stats = df.describe(include='all').transpose()
    summary_stats.to_string(file)  # write dataframe as string directly to file
    file.write("\n\n")

    # Categorical Variables
    file.write("# Categorical Variables\n")
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        file.write(f"Most Common Value for {col}: {df[col].mode()[0]}\n")
    file.write("\n")

    # Missing Values
    file.write("# Missing Values\n")
    file.write(f"Number of Missing or Null Values by Column:\n{df.isnull().sum()}\n")
    file.write("\n")
    
file.close()
