
# Required Libraries
import pandas as pd

# Load Dataset
dataset = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Initialize file for writing outputs
output_file = open("data_exploration.txt", "w")

# Calculate the Data Size
data_size = "# Data Size\nRows: " + str(dataset.shape[0]) +", Columns: " + str(dataset.shape[1]) + "\n"
output_file.write(data_size)

# Calculating Summary Statistics
summary_stats = "# Summary Statistics\n"
output_file.write(summary_stats)
dataset.describe(include='all').to_string(output_file)

# Calculate Categorical Variables
categorical_variables = dataset.select_dtypes(include=['object']).columns
common_values = "\n# Categorical Variables\n"
for variable in categorical_variables:
    common_values += ("Most common value of " + variable + ": " + str(dataset[variable].mode()[0]) + "\n")
output_file.write(common_values)

# Calculate Missing Values
missing_values = dataset.isnull().sum()

# Count of special numeric unknown/undefined values
# According to the dataset description, the original BRFSS dataset removed rows with missing values,
# so no special handling is necessary here
missing_values_str = "\n# Missing Values\n" + str(missing_values[missing_values > 0]) + "\n"
output_file.write(missing_values_str)

output_file.close()
