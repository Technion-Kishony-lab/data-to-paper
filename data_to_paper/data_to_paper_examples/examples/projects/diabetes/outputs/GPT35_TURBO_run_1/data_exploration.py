
import pandas as pd
import numpy as np

# Load the dataset
data = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Create an output file to write the data exploration summary
output_file = open("data_exploration.txt", "w")

# Data Size
data_size = data.shape
output_file.write("# Data Size\n")
output_file.write(f"Number of Rows: {data_size[0]}\n")
output_file.write(f"Number of Columns: {data_size[1]}\n\n")

# Summary Statistics
summary_stats = data.describe()
output_file.write("# Summary Statistics\n")
output_file.write(summary_stats.to_string())
output_file.write("\n\n")

# Categorical Variables
categorical_vars = ["Diabetes_binary", "HighBP", "HighChol", "CholCheck", "Smoker", "Stroke", "HeartDiseaseorAttack", 
                    "PhysActivity", "Fruits", "Veggies", "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost", 
                    "GenHlth", "DiffWalk", "Sex", "Age", "Education", "Income"]

output_file.write("# Categorical Variables\n")
for var in categorical_vars:
    output_file.write(f"{var}\n")
    output_file.write(f"Most Common Values:\n{data[var].value_counts(normalize=True).head()}\n\n")

# Missing Values
missing_values_count = data.isnull().sum()
output_file.write("# Missing Values\n")
output_file.write(missing_values_count.to_string())
output_file.write("\n\n")

# Close the output file
output_file.close()
