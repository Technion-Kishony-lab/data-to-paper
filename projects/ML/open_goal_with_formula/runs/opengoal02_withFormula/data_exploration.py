
import pandas as pd
import numpy as np

# Constants
CSV_FILE = "tracheal_tube_insertion.csv"
OUTPUT_FILE = "data_exploration.txt"

# Load the dataset into a pandas dataframe
data = pd.read_csv(CSV_FILE)

# Open the output file in write mode
with open(OUTPUT_FILE, 'w') as file:

    # Data Size
    file.write('# Data Size\n')
    file.write('Total number of rows: {}\n'.format(len(data)))
    file.write('Total number of columns: {}\n\n'.format(len(data.columns)))

    # Summary Statistics
    file.write('# Summary Statistics\n')
    file.write('{}\n\n'.format(data.describe()))

    # Categorical Variables
    file.write('# Categorical Variables\n')
    file.write('Sex most common value: {}\n\n'.format(data['sex'].mode().values[0]))

    # Missing Values
    file.write('# Missing Values\n')
    missing_values = data.isnull().sum()
    file.write('{}\n\n'.format(missing_values))
    
    # Check for special numeric values that stand for unknown/undefined
    for col in data.columns:
        if data[col].dtype == np.number:
            file.write("Undefined/unknown values in {}: {}\n".format(col, (data[col] == -1).sum()))
