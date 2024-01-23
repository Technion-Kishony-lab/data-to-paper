
# Import the necessary modules
import pandas as pd
import numpy as np

# Load the data 
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open file in write mode
with open('data_exploration.txt', 'w') as file:
  # Data Size
  file.write('# Data Size\n')
  num_rows = len(df)
  num_cols = df.shape[1]
  file.write(f'Number of rows: {num_rows}\n')
  file.write(f'Number of columns: {num_cols}\n\n')

  # Summary Statistics
  file.write('# Summary Statistics\n')
  summary_stats = df.describe()
  # Convert summary_stats dataframe to string and write to file
  file.write(f'{summary_stats}\n\n')

  # Categorical Variables
  file.write('# Categorical Variables\n')
  # List of categorical features
  categorical_features = df.select_dtypes(include=['object','bool']).columns.tolist()
  for feature in categorical_features:
    most_common_cat = df[feature].mode().values[0]
    file.write(f'Feature "{feature}" most common value: {most_common_cat}\n')
  if not categorical_features:
    file.write('No categorical features\n')
  file.write('\n')

  # Missing Values
  file.write('# Missing Values\n')
  missing_values = df.isnull().sum()
  total_missing = missing_values.sum()
  if total_missing > 0:
    file.write(f'Total missing values: {total_missing}\n')
    file.write(f'Missing values by feature:\n {missing_values}\n')
  else:
    file.write('No missing values\n')
