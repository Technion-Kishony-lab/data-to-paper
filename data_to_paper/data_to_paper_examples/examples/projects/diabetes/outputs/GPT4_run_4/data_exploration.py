
import pandas as pd
import numpy as np

# Load the data into a pandas DataFrame
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Open a text file named 'data_exploration.txt' to write all our findings from this prescriptive analysis
output_file = open('data_exploration.txt', 'w')

# Data Size
output_file.write('# Data Size\n')
output_file.write('Number of rows: ' + str(df.shape[0]) + '\n')
output_file.write('Number of columns: ' + str(df.shape[1]) + '\n\n')

# Summary Statistics
output_file.write('# Summary Statistics\n')
summary_stats = df.describe()
output_file.write(str(summary_stats) + '\n\n')

# Categorical Variables
output_file.write('# Categorical Variables\n')
categorical_vars = df.select_dtypes(include=['object'])
for i in categorical_vars.columns:
    output_file.write('Column: '+i+'\n')
    output_file.write(str(df[i].value_counts().head()) + '\n')
output_file.write('\n')

# Missing Values
output_file.write('# Missing Values\n')
missing_vals = df.isnull().sum()
output_file.write(str(missing_vals[missing_vals > 0]) +'\n\n')

# Special numeric values
output_file.write('# Special Numeric Values\n')
for column in df.columns:
    output_file.write('Column: ' + column + '\n')
    numerical_vals = df[column]._get_numeric_data()
    output_file.write(str(numerical_vals.value_counts().head()) + '\n')
output_file.write('\n')

output_file.close()
