
import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open our output file
with open('data_exploration.txt', mode='w') as f:

    # Data Size
    shape = df.shape
    f.write('# Data Size\n')
    f.write(f'Rows: {shape[0]}, Columns: {shape[1]}\n\n')
    
    # Summary Statistics
    f.write('# Summary Statistics\n')
    desc = df.describe(include='all')
    f.write(f'{desc}\n\n')
    
    # Check categorical variables
    f.write('# Categorical Variables\n')
    categorical = df.select_dtypes(include=['object'])
    for name in categorical.columns:
        top_5 = df[name].value_counts().nlargest(5)
        f.write(f'{name}: \n{top_5}\n\n')
    
    # Missing Values
    f.write('# Missing Values\n')
    total_missing = df.isnull().sum().sum()
    f.write(f'Total missing/undefined values: {total_missing}\n')
    
    # Check for special numeric values stand for unknown/undefined if any
    f.write('Unknown/Undefined numeric values:\n')
    for col in df.select_dtypes(include=[np.number]):
        unknowns = df[col].isin([-999, -9999]).sum()
        if unknowns > 0:
            f.write(f'{col}: {unknowns} Unknown/Undefined values\n')
    
    # Count of each sex
    f.write('\n# Sex Distribution\n')
    sex_count = df['sex'].value_counts()
    f.write(f'Males: {sex_count[1]}, Females: {sex_count[0]}\n')
