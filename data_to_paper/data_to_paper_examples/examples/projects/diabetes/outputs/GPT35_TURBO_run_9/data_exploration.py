
import pandas as pd

# Read the dataset
data = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Open the output file
output_file = open('data_exploration.txt', 'w')

# Data Size
output_file.write("# Data Size\n")
output_file.write(f"Number of rows: {len(data)}\n")
output_file.write(f"Number of columns: {len(data.columns)}\n")
output_file.write("\n")

# Summary Statistics
output_file.write("# Summary Statistics\n")
summary_stats = data.describe(include='all')
output_file.write(summary_stats.to_string())
output_file.write("\n")

# Categorical Variables
output_file.write("# Categorical Variables\n")
categorical_vars = ['Sex', 'Age', 'Education', 'Income']
for var in categorical_vars:
    output_file.write(f"{var}: {data[var].value_counts().to_string()}\n")
output_file.write("\n")

# Missing Values
output_file.write("# Missing Values\n")
null_counts = data.isnull().sum()
output_file.write(null_counts.to_string())
output_file.write("\n")

# Close the output file
output_file.close()
