
import pandas as pd
import numpy as np

# Read in the tracheal_tube_insertion.csv file
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open the file for writing the results
with open('data_exploration.txt', 'w') as file:

    # Add data size
    file.write('# Data Size\n')
    file.write(f'Number of Rows: {df.shape[0]}\n')
    file.write(f'Number of Columns: {df.shape[1]}\n\n')

    # Add summary statistics
    file.write('# Summary Statistics\n')
    file.write(df.describe().to_string())
    file.write('\n\n')

    # Manually identify the categorical variables [based on the provided dataset description]
    categorical_vars = ['sex', 'tube']

    # Add categorical variables
    file.write('# Categorical Variables\n')
    for var in categorical_vars:
        file.write(f'Top 5 Most Common Values for {var}:\n')
        file.write(df[var].value_counts().head().to_string())
        file.write('\n\n')

    # Add missing values
    file.write('# Missing Values\n')
    for column in df.columns:
        missing_value = df[column].isna().sum()
        file.write(f'Number of Missing Values in {column}: {missing_value}\n')
    file.write('\n')

    # No other subjects were mentioned in the prompt, so not adding any other summary values
