
import pandas as pd

# Load dataset
data = pd.read_csv("tracheal_tube_insertion.csv")

# Create a text file
output_file = open("data_exploration.txt", "w")

# Data Size
output_file.write("# Data Size\n")
output_file.write(f"Number of rows: {data.shape[0]}\n")
output_file.write(f"Number of columns: {data.shape[1]}\n\n")

# Summary Statistics
output_file.write("# Summary Statistics\n")
summary_stats = data.describe()
output_file.write(summary_stats.to_string())
output_file.write("\n\n")

# Categorical Variables
output_file.write("# Categorical Variables\n")
categorical_vars = data.select_dtypes(include=['object'])
for column in categorical_vars:
    output_file.write(f"For {column}, most common value: {data[column].mode()[0]}\n")
output_file.write("\n")

# Missing values
output_file.write("# Missing Values\n")
missing_values = data.isnull().sum()
output_file.write(missing_values.to_string())
output_file.write("\n\n")

output_file.close()
