
import pandas as pd
import numpy as np

# Load the data
data = pd.read_csv('tracheal_tube_insertion.csv')

# Define output file
f = open("data_exploration.txt", "w")

# Measure of the scale of our data (e.g., number of rows, number of columns)
f.write("# Data Size\n")
f.write(f'Number of rows: {data.shape[0]}\n')
f.write(f'Number of columns: {data.shape[1]}\n')

# Summary statistics of all or key variables
f.write("\n# Summary Statistics\n")
summaryStats = data.describe().transpose()
summaryStats.to_string(f)

# Categorical Variables
f.write("\n# Categorical Variables\n")
sex_counts = data['sex'].value_counts()
f.write(f'Sex counts:\n{sex_counts}\n')

# Missing Values
f.write("\n# Missing Values\n")
missing_values_count = data.isnull().sum()
f.write(f'Missing values count:\n{missing_values_count}\n')

# check for any special numeric values that stand for unknown 
# if any based on dataset description
f.write("\n# Special Numeric Values\n")
special_values_count = (data < 0).sum()
f.write(f'Special values count:\n{special_values_count}\n')

f.close()
