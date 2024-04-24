
import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv("tracheal_tube_insertion.csv") 

# Calculate summary statistics
data_size = df.shape
summary_stats = df.describe()
missing_values = df.isnull().sum()

# Find out unique counts for categorical variables
categorical_vars = df.select_dtypes(include='object') # Assuming that categorical variables are of object data type
categorical_counts = categorical_vars.apply(lambda x: x.value_counts().idxmax())

# Saving output to txt file

with open('data_exploration.txt', 'w') as f:
    f.write('# Data Size\n')
    f.write(f'Number of Rows: {data_size[0]}, Number of Columns: {data_size[1]}\n\n')

    f.write('# Summary Statistics\n')
    f.write(str(summary_stats)+'\n\n')

    if not categorical_vars.empty:
        f.write('# Categorical Variables\n')
        for var, val in categorical_counts.items():
            f.write(f'Most common value for {var}: {val}\n')
        f.write('\n')
    else:
        f.write('# Categorical Variables\n')
        f.write('# Not Applicable\n\n')

    f.write('# Missing Values\n')
    for var, val in missing_values.items():
        if val > 0:
            f.write(f'Number of missing values for {var}: {val}\n')
    mismatch_vals = df[(df.age_c<0) | (df.ht<0) | (df.wt<0) | (df.tube_depth_G<0)]
    if len(mismatch_vals)>0:
        f.write(f'Rows with non-logical negative values: {len(mismatch_vals)}\n')
    else:
        f.write('No missing, unknown or illogical values found.\n')
    f.close()
