
import pandas as pd

# Reading the data
data = pd.read_csv('tracheal_tube_insertion.csv')

# Open the file with write permission
file = open("data_exploration.txt", "w")

# Data Size
file.write("# Data Size\n")
file.write(f'Number of rows: {data.shape[0]}\n')
file.write(f'Number of columns: {data.shape[1]}\n')

# Summary Statistics
file.write('\n# Summary Statistics\n')
summary_stats = data.describe(include='all')
file.write(f'{summary_stats}\n')

# Categorical Variables 
file.write('\n# Categorical Variables\n')
categorical_variables = data.select_dtypes(include = 'object')
mode = categorical_variables.mode().to_string(header = False, index = False)
if mode: 
    file.write(mode + '\n')
else:
    file.write('# Not Applicable\n')

# Missing Values
file.write('\n# Missing Values\n')
missing_values = data.isnull().sum().sum()
file.write(f'Total missing values: {missing_values}\n')

# Special Numeric Values
file.write('\n# Special Numeric Values\n')
# Here we assume that 'tube' is the only special numeric features that stand for unknown (as per dataset description)
special_numbers = data['tube'].isnull().sum()
file.write(f'Special numeric values in tube: {special_numbers}\n')

file.close()
