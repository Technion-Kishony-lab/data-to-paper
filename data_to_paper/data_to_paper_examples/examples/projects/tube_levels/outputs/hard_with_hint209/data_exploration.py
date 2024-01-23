
# start with importing the required libraries
import pandas as pd
import numpy as np

# load your dataset
data = pd.read_csv('tracheal_tube_insertion.csv')

# get the data size
data_size = data.shape

# get the summary statistics
summary_stats = data.describe(include='all')

# identify categorical variables 
categorical_variables = data.select_dtypes(include=['object'])

# find common values
common_values = categorical_variables.mode()

# get the count of missing values 
missing_values = data.isnull().sum()

# writing the output to a text file
with open('data_exploration.txt', 'w') as file:
    
    file.write("# Data Size\n")
    file.write(f"Number of Rows : {data_size[0]}\n")
    file.write(f"Number of Columns : {data_size[1]}\n\n")
    
    file.write("# Summary Statistics\n")
    file.write(str(summary_stats))
    file.write("\n\n")
    
    file.write("# Categorical Variables\n")
    if categorical_variables.empty:
        file.write("No categorical variables in the dataset\n\n")
    else:
        for col in categorical_variables:
            file.write(f"{col} - Most common value: {common_values[col][0]}")
            file.write("\n\n")
    
    file.write("# Missing Values\n")
    if missing_values.sum() == 0:
        file.write("No missing values in the dataset\n")
    else:
        file.write(str(missing_values))
        file.write("\n")
