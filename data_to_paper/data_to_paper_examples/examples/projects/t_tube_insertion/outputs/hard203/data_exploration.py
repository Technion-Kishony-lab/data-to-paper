
import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open file to save output
with open('data_exploration.txt', 'w') as file:
    
    # Data size
    file.write('# Data Size\n')
    file.write(f'Number of rows: {df.shape[0]}\n')
    file.write(f'Number of columns: {df.shape[1]}\n\n')

    # Summary statistics
    file.write('# Summary Statistics\n')
    summary_stats = df.describe(include='all')
    file.write(f'{summary_stats}\n\n')
    
    # Categorical variables 
    file.write('# Categorical Variables\n')
    categorical_cols = df.select_dtypes(include=['object','bool']).columns
    if len(categorical_cols) == 0:
        file.write("There are no categorical variables in the dataset.\n")
    else:
        for cat in categorical_cols:
            mode = df[cat].mode().values[0]
            file.write(f'Most common value in {cat}: {mode}\n')
    file.write('\n')

    # Missing values
    file.write('# Missing Values\n')
    missing_values = df.isnull().sum()
    if missing_values.sum() == 0:
        file.write("There are no missing values in the dataset.\n")
    else:
        file.write(f'{missing_values}\n')
    
# close the file
file.close()
