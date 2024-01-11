

# Import Required Libraries
import pandas as pd

# Load Data
data = pd.read_csv('tracheal_tube_insertion.csv')

# Open File for Writing
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write('# Data Size\n')
    rows, columns = data.shape
    f.write('Number of rows: {}\n'.format(rows))
    f.write('Number of columns: {}\n'.format(columns))

    # Summary Statistics
    f.write('\n# Summary Statistics\n')
    summary = data.describe()
    f.write('{}\n'.format(summary))

    # Categorical Variables
    f.write('\n# Categorical Variables\n')
    f.write("Categorical Variable 'sex', most common value: '{}'\n".format(data['sex'].mode()[0]))

    # Missing Values
    f.write('\n# Missing Values\n')
    missing_values = data.isnull().sum()
    f.write('{}\n'.format(missing_values))

