
import pandas as pd
import numpy as np

# Read the .csv file with pandas
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Open file to write the summary
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write('# Data Size\n')
    f.write('Number of Rows: {}\n'.format(df.shape[0]))
    f.write('Number of Columns: {}\n\n'.format(df.shape[1]))
    
    # Summary Statistics
    f.write('# Summary Statistics\n')
    summary_stats = df.describe()
    summary_stats.to_string(f)
    f.write('\n')

    # Categorical Variables
    f.write('# Categorical Variables\n')
    categorical_columns = df.select_dtypes(include=['category', 'object']).columns
    for col in categorical_columns:
        top_freq = df[col].mode()[0]
        f.write('Most frequent in {}: {}\n'.format(col, top_freq))
    f.write('\n')

    # Missing Values
    f.write('# Missing Values\n')
    missing_values = df.isnull().sum()
    for col, mv in missing_values.items():
        if mv > 0:
            f.write('Missing in {}: {}\n'.format(col, mv))
    f.write('\n')

    # Special Numeric Values
    f.write('# Special Numeric Values\n')
    for col, _def in df.dtypes.items():
        if _def in ['int64', 'float64']:
            special_count = df[df[col] < 0].shape[0]
            if special_count > 0:
                f.write('Special values in {}: {}\n'.format(col, special_count))
    f.write('\n')            

f.close()            
