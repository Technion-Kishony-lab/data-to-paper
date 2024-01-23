
import pandas as pd
import numpy as np

# Load data
data = pd.read_csv('tracheal_tube_insertion.csv')

# Open file to save results
output_file = open("data_exploration.txt", "w")

# Get the size of our data
numberOfRows = len(data.index)
numberOfColumns = len(data.columns)

output_file.write("# Data Size\n")
data_size = "Number of Rows: {}, Number of Columns: {}".format(numberOfRows, numberOfColumns)
output_file.write(data_size)
output_file.write("\n\n")

# Get summary statistics
output_file.write("# Summary Statistics\n")
summary_stats = data.describe()
output_file.write(summary_stats.to_string())
output_file.write("\n\n")

# Categorical Variables
output_file.write("# Categorical Variables\n")
categorical_values = data['sex'].value_counts()
output_file.write(str(categorical_values))
output_file.write("\n\n")

# Missing values check
output_file.write("# Missing Values\n")
missing_values = data.isnull().sum()
output_file.write(str(missing_values))
output_file.write("\n")

# Close output file
output_file.close()
