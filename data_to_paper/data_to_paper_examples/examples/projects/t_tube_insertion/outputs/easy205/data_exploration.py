
# Importing Required Libraries
import pandas as pd
import numpy as np

# loading the dataset
data = pd.read_csv('tracheal_tube_insertion.csv')

# Write to "data_exploration.txt" file
with open('data_exploration.txt', 'w') as file:

    # Find rows and columns in the data
    rows, cols = data.shape
    file.write("# Data Size")
    file.write(f"\nNumber of Rows: {rows}")
    file.write(f"\nNumber of Columns: {cols}")

    # Summary Statistics
    file.write("\n\n# Summary Statistics")
    summary_stats = data.describe(include='all')
    summary_stats.to_string(file)

    # Categorical Variables - Dataset has no conventional categorical columns,
    # however, the sex column could be considered one. Let's examine it further.
    file.write("\n\n# Categorical Variables")
    file.write("\nExamining 'sex' Column:")
    most_common_value = data['sex'].value_counts().idxmax()
    frequecy_of_most_common_value = data['sex'].value_counts().max()
    file.write(f"\nThe most common value is '{most_common_value}' with frequency {frequecy_of_most_common_value}.")
      
    # Missing Values
    file.write("\n\n# Missing Values")
    missing_values = data.isnull().sum()
    missing_values.to_string(file)
