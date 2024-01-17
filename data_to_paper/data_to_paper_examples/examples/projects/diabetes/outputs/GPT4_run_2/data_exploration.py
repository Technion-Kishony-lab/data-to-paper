
# Required libraries
import pandas as pd

# Load the data into a pandas data frame
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Creates and Opens a file named "data_exploration.txt" in "write mode"
f = open("data_exploration.txt", 'w')

# Data Size
f.write('# Data Size\n')
f.write('Number of Rows: {}\n'.format(df.shape[0]))
f.write('Number of Columns: {}\n\n'.format(df.shape[1]))

# Summary Statistics
f.write('# Summary Statistics\n')
describe = df.describe()
f.write('{}\n\n'.format(describe))

# Categorical Variables
cat_vars = df.select_dtypes(include=['bool']).columns
f.write('# Categorical Variables\n')
for var in cat_vars:
    f.write('{}: {}\n'.format(var, df[var].mode().values[0]))
f.write('\n')

# Missing Values
f.write('# Missing Values\n')
miss_val = df.isnull().sum()
f.write('{}\n\n'.format(miss_val))

# Special numeric values for unknown/undefined 
f.write('# Special numeric values for unknown/undefined\n')
for column in df.columns:
    f.write('Column: {}, Values: {}\n'.format(column,df[df[column] < 0][column].unique()))
f.write('\n')

f.close()
