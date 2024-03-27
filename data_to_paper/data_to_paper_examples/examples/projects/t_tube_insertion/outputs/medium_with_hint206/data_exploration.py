
import pandas as pd
import numpy as np
from scipy import stats

# Load data
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open the output file
with open('data_exploration.txt', 'w') as file:

    # Data Size
    file.write('# Data Size\n')
    file.write(f'Number of rows: {df.shape[0]}\n')
    file.write(f'Number of columns: {df.shape[1]}\n\n')

    # Summary Statistics
    file.write('# Summary Statistics\n')
    description = df.describe()
    for column in description.columns:
        file.write(f'{column}:\n')
        file.write(f'min: {description[column]["min"]}\n')
        file.write(f'25%: {description[column]["25%"]}\n')
        file.write(f'50%: {description[column]["50%"]}\n')
        file.write(f'75%: {description[column]["75%"]}\n')
        file.write(f'max: {description[column]["max"]}\n\n')

    # Categorical Variables
    file.write('# Categorical Variables\n')
    categorical_columns = df.select_dtypes(include=['object']).columns
    for column in categorical_columns:
        most_common = df[column].value_counts().index[0]
        file.write(f'The most common value for {column} is: {most_common}\n\n')

    # Missing Values
    file.write('# Missing Values\n')
    missing_values = df.isna().sum()
    for column in missing_values.index:
        file.write(f'Number of missing values for {column}: {missing_values[column]}\n\n')
