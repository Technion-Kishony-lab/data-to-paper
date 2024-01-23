
import pandas as pd
import numpy as np
import scipy as sp

# Load the data
data = pd.read_csv("tracheal_tube_insertion.csv")

# Open the file "data_exploration.txt" to write
with open("data_exploration.txt", "w") as file:
    
    # Data size
    file.write("# Data Size\n")
    file.write(f"Number of rows: {data.shape[0]}\n")
    file.write(f"Number of columns: {data.shape[1]}\n\n")

    # Summary statistics
    file.write("# Summary Statistics\n")
    summary_stats = data.describe().transpose()
    summary_stats.to_string(file)  # Output summary stats to the file
    file.write("\n\n")
    
    # Categorical Variables
    file.write("# Categorical Variables\n")
    categorical_columns = data.select_dtypes(include=['object', 'bool']).columns.tolist()
    for column in categorical_columns:
        file.write(f"For the variable '{column}', the most common value is: {data[column].mode()[0]}\n")
    if not categorical_columns:  # If there are no categorical columns
        file.write("There are no categorical variables in the dataset.\n")
    file.write("\n")
    
    # Missing Values
    file.write("# Missing Values\n")
    missing_values = data.isnull().sum()
    missing_values.to_string(file)  # Output missing values to the file
    if missing_values.sum() == 0:  # If there are no missing values
        file.write("There are no missing values in the dataset.\n")
