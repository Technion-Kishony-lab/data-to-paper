
# Import necessary packages
import pandas as pd

# Read data
data = pd.read_csv('tracheal_tube_insertion.csv')

# Open file
with open('data_exploration.txt', 'w') as file:
    # Write data size information to file
    file.write('# Data Size\n')
    file.write('Number of rows: {}\n'.format(data.shape[0]))
    file.write('Number of columns: {}\n'.format(data.shape[1]))
    file.write('\n')

    # Write summary statistics
    file.write('# Summary Statistics\n')
    summary_statistics = data.describe()
    summary_statistics.round(2).to_string(file)  # rounding to 2 decimal places for neatness
    file.write('\n')

    # Write categorical variables to file
    file.write('# Categorical Variables\n')
    categorical_variables = data.select_dtypes(include=['object', 'bool']).columns.tolist()
    if categorical_variables:  # if there are categorical variables in the dataset
        for var in categorical_variables:
            file.write('Most common value(s) in `{}`: {}\n'.format(var, data[var].mode().to_list()))
    else:
        file.write('There are no categorical variables in this dataset.\n')
    file.write('\n')

    # Write missing values to file
    file.write('# Missing Values\n')
    missing_values = data.isna().sum()
    missing_values.to_string(file)
