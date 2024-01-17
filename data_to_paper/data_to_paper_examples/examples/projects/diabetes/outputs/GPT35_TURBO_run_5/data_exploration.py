
import pandas as pd
import numpy as np

# Load the dataset
data = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Create an output file
output_file = open("data_exploration.txt", "w")

# Measure of the scale of our data
data_size = f"Data Size: {data.shape[0]} rows, {data.shape[1]} columns"
output_file.write("# Data Size\n")
output_file.write(data_size + "\n\n")

# Summary Statistics
summary_statistics = data.describe().to_string()
output_file.write("# Summary Statistics\n")
output_file.write(summary_statistics + "\n\n")

# Categorical Variables
categorical_values = ["Diabetes_binary", "HighBP", "HighChol", "CholCheck", "PhysActivity", "Fruits", "Veggies", "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost", "GenHlth", "DiffWalk", "Sex", "Age", "Education", "Income"]

output_file.write("# Categorical Variables\n")
for cat_var in categorical_values:
    most_common_values = data[cat_var].value_counts().head(5)
    output_file.write(f"{cat_var}: {most_common_values.to_string()}\n\n")

# Missing Values
missing_values = data.isnull().sum().to_string()
output_file.write("# Missing Values\n")
output_file.write(missing_values)

output_file.close()
