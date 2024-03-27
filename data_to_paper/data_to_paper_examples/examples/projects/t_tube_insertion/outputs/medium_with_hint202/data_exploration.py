
# Import necessary libraries
import pandas as pd
import numpy as np

# Load data
data = pd.read_csv('tracheal_tube_insertion.csv')

# Open file for writing
f = open('data_exploration.txt', 'w')

# Write size of data
f.write('# Data Size \n')
f.write('Number of Rows: {}\n'.format(data.shape[0]))
f.write('Number of Columns: {}\n'.format(data.shape[1]))
f.write('\n')

# Write summary statistics
f.write('# Summary Statistics \n')
desc = data.describe(include='all')
f.write('{}\n'.format(desc))
f.write('\n')

# Categorical Variables
f.write('# Categorical Variables \n')
categorical = data.select_dtypes(include=['object', 'category'])
categorical_columns = categorical.columns.tolist()
for column in categorical_columns:
    f.write('Most Common Value in {}: {}\n'.format(column, data[column].mode()[0]))
f.write('\n')

# Check for missing values
f.write('# Missing Values \n')
missing_values = data.isna().sum()
f.write('{}\n'.format(missing_values))
f.write('\n')

# Close file
f.close()
