
import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open the summary file
with open('data_exploration.txt', 'w') as f:

    # Data size
    f.write('# Data Size\n')
    f.write(f'Number of rows: {df.shape[0]}\n')
    f.write(f'Number of columns: {df.shape[1]}\n\n')

    # Summary statistics
    f.write('# Summary Statistics\n')
    summary_statistics = df.describe(include=[np.number])
    summary_statistics.to_string(f)
    f.write('\n')

    # Categorical variables
    categorical_variables = df.select_dtypes(include=['bool', 'object'])

    # If there is any categorical variable
    if not categorical_variables.empty:
        f.write('# Categorical Variables\n')
        for var in categorical_variables.columns:
            f.write(f'{var} value counts:\n')
            f.write(f'{categorical_variables[var].value_counts()}\n')
        f.write('\n')

    # If no categorical variable is available
    else:
        f.write('# Categorical Variables\n')
        f.write('There are no categorical variables in the data.\n\n')

    # Missing values
    f.write('# Missing Values\n')
    missing_values = df.isnull().sum()
    missing_values.to_string(f)
    f.write('\n')
