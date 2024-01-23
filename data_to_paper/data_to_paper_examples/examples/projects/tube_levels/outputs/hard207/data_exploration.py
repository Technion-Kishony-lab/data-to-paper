
import pandas as pd
import numpy as np

# data loading
data = pd.read_csv('tracheal_tube_insertion.csv')

# open an output file to save summary statistics
output_file = open("data_exploration.txt", "w")

# Data Size
output_file.write("# Data Size\n")
output_file.write(f"Number of Rows: {data.shape[0]}\n")
output_file.write(f"Number of Columns: {data.shape[1]}\n\n")

# Summary Statistics
numeric_cols = data.select_dtypes(include=[np.number]).columns
output_file.write("# Summary Statistics\n")
for col in numeric_cols:
    output_file.write(f"For {col}\n")
    output_file.write(f"Mean: {data[col].mean()}\n")
    output_file.write(f"Standard Deviation: {data[col].std()}\n\n")
 
#Categorical Variables
categorical_cols = data.select_dtypes(include=['object']).columns
output_file.write("# Categorical Variables\n")
for col in categorical_cols:
    output_file.write(f"For {col}\n")
    output_file.write(f"Most common values:\n")
    output_file.write(f"{data[col].value_counts().head().to_string()}\n\n")

# Missing Values
output_file.write("# Missing Values\n")
output_file.write("Counts of missing, unknown, or undefined values\n")
output_file.write(f"{data.isnull().sum().to_string()}\n\n")

# Close file
output_file.close()

