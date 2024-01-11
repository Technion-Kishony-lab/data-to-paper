
# Required Libraries
import pandas as pd

# Reading Data
df = pd.read_csv('tracheal_tube_insertion.csv')

# Data Size
data_size = df.shape

# Summary Statistics
summary_stats = df.describe(include='all')

# Categorical Variables
cat_vars = df.select_dtypes(include=['object']).columns
cat_vals = {}
for col in cat_vars:
    cat_vals[col] = df[col].value_counts().idxmax()

# Missing Values
missing_vals = df.isnull().sum()

# Writing to text file
with open('data_exploration.txt', 'w') as file:
    file.write("# Data Size\n")
    file.write(f'Number of Rows: {data_size[0]}\n')
    file.write(f'Number of Columns: {data_size[1]}\n\n')

    file.write("# Summary Statistics\n")
    file.write(f'{summary_stats}\n\n')

    file.write("# Categorical Variables\n")
    if cat_vars.empty:
        file.write('No categorical variables\n\n')
    else:
        for col, val in cat_vals.items():
            file.write(f'{col} has maximum values of {val}\n\n')

    file.write("# Missing Values\n")
    num_missing = missing_vals.sum()
    if num_missing == 0:
        file.write('No missing values\n')
    else:
        for col, val in missing_vals.items():
            if val > 0:
                file.write(f'{col} has {val} missing values\n')
