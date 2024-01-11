
import pandas as pd
import numpy as np

# load the data
data = pd.read_csv('tracheal_tube_insertion.csv')

# prepare the summary statistics
summary_stats = data.describe(include='all')

# count the missing/unknown or undefined values
missing_values = data.isnull().sum()

# count distinct values for categorical variables
sex_counts = data['sex'].value_counts()

# count special numeric values
special_numeric_values = data['tube'].value_counts()

# count total number of rows and columns
num_rows = len(data)
num_columns = len(data.columns)

# write to a txt file
with open('data_exploration.txt', 'w') as file:
    file.write('# Data Size\n')
    file.write('Number of Rows: {}\n'.format(num_rows))
    file.write('Number of Columns: {}\n\n'.format(num_columns))

    file.write('# Summary Statistics\n')
    file.write('{}\n\n'.format(summary_stats))

    file.write('# Categorical Variables\n')
    file.write('sex:\n{}\n\n'.format(sex_counts.to_string()))

    file.write('# Missing Values\n')
    file.write('{}\n\n'.format(missing_values.to_string()))

    file.write('# Special Numeric Values\n')
    file.write('tube:\n{}\n'.format(special_numeric_values.to_string()))
