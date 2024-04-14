
import pandas as pd
import numpy as np

# Load the data
data = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# Open the output file
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write('# Data Size\n')
    f.write('Number of Rows: {}\n'.format(data.shape[0]))
    f.write('Number of Columns: {}\n\n'.format(data.shape[1]))
    
    # Data Types
    f.write('# Data Types\n')
    f.write('Data Types of Variables:\n')
    f.write(data.dtypes.to_string() + '\n\n')

    # Summary Statistics for Numeric Variables
    f.write('# Summary Statistics for Numeric Variables\n')
    numeric_data = data.select_dtypes(include=['int64', 'float64'])
    f.write('Number of Numeric Variables: {}\n'.format(len(numeric_data.columns)))
    for col in numeric_data.columns:
        f.write(f'{col}: Mean={numeric_data[col].mean():.2f}, Median={numeric_data[col].median():.2f}, Std={numeric_data[col].std():.2f}\n')
    f.write('\n')

    # Summary Statistics for Categorical Variables
    f.write('# Summary Statistics for Categorical Variables\n')
    categorical_data = data.select_dtypes(include=['object'])
    f.write('Number of Categorical Variables: {}\n'.format(len(categorical_data.columns)))
    for col in categorical_data.columns:
        f.write(f'{col}: Number of unique categories={categorical_data[col].nunique()}, Most common category={categorical_data[col].mode()[0]}\n')
    f.write('\n')
     
    # Categorical Variables
    f.write('# Categorical Variables\n')
    categorical_variables = data.select_dtypes(include='object')
    for col in categorical_variables.columns:
        f.write(f'Variable: {col}, Unique categories: {categorical_variables[col].nunique()}, Most frequent category: {categorical_variables[col].mode()[0]}\n')
    f.write('\n')
    
    # Missing Values
    f.write('# Missing Values\n')
    missing_values = data.isnull().sum()
    total_missing = missing_values.sum()
    if total_missing > 0:
        f.write('Total missing or undefined values in the data: {}\n'.format(total_missing))
        for col in data.columns:
            missing = missing_values[col]
            if missing > 0:
                f.write(f'{col}: Missing={missing}, Percentage={missing/data.shape[0]*100:.2f}%\n')
    else:
        f.write('No missing values in the data.\n')

