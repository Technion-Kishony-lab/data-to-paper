
import pandas as pd
import numpy as np

# Load data
data = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Output file
out_file = open("data_exploration.txt", "w")

# Data size
out_file.write("# Data Size\n")
out_file.write("Number of Rows: " + str(data.shape[0]) + "\n")
out_file.write("Number of Columns: " + str(data.shape[1]) + "\n")

# Summary Statistics
summary_stats = data.describe(include='all')

out_file.write("\n# Summary Statistics\n")
out_file.write(str(summary_stats) + "\n")

# Categorical Variables
cat_vars = data.select_dtypes(include=['bool', 'object']).columns

out_file.write("\n# Categorical Variables\n")
for var in cat_vars:
  out_file.write("\n" + var + ":\n")
  out_file.write(data[var].value_counts().to_string())

# Missing Values
out_file.write("\n\n# Missing Values\n")
missing_vals = data.isnull().sum()

out_file.write(missing_vals.to_string() + "\n")

out_file.close()
