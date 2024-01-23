
# Import necessary libraries
import pandas as pd
import numpy as np

# Load data
data = pd.read_csv('tracheal_tube_insertion.csv')

output = {}
output['# Data Size'] = 'No. of Rows: {}, No. of Columns: {}'.format(*data.shape)

output['# Summary Statistics'] = 'Mean, Min, Max of each of the numerical columns:\n' + data.describe().loc[['mean','min','max']].to_string()

# Get unique values for categorical variables if any
categorical_columns = ['sex']
output['# Categorical Variables'] = ''
for column in categorical_columns:
    output['# Categorical Variables'] += f'{column}:\n{data[column].value_counts().head().to_string()}\n'

# Check for missing values
output['# Missing Values'] = 'Missing Values Count:\n' + data.isna().sum().to_string()

# other summaries
output['# Target Statistics'] = 'Mean, Min, Max of the target column (tube_depth_G):\n' + data['tube_depth_G'].describe().loc[['mean','min','max']].to_string()

# Save this overview/summary to a text file
with open('data_exploration.txt', 'w') as f:
    for key in output:
        f.write(f'{key}\n{output[key]}\n\n')
