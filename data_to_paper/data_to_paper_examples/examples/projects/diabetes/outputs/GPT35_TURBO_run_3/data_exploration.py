
import pandas as pd
import numpy as np

# Read the dataset
data = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Open the output file for writing
output_file = open('data_exploration.txt', 'w')

# Data Size
output_file.write("# Data Size\n")
output_file.write("Number of rows: {}\n".format(len(data)))
output_file.write("Number of columns: {}\n".format(len(data.columns)))
output_file.write("\n")

# Summary Statistics
output_file.write("# Summary Statistics\n")
output_file.write(data.describe().to_string())
output_file.write("\n")

# Categorical Variables
output_file.write("# Categorical Variables\n")
categorical_vars = ['Diabetes_binary', 'HighBP', 'HighChol', 'CholCheck', 'Smoker',
                    'Stroke', 'HeartDiseaseorAttack', 'PhysActivity', 'Fruits',
                    'Veggies', 'HvyAlcoholConsump', 'AnyHealthcare', 'NoDocbcCost',
                    'GenHlth', 'DiffWalk', 'Sex', 'Age', 'Education', 'Income']
for var in categorical_vars:
    value_counts = data[var].value_counts()
    output_file.write("{}:\n".format(var))
    output_file.write(value_counts.to_string())
    output_file.write("\n")

# Missing Values
output_file.write("# Missing Values\n")
missing_values = data.isnull().sum()
output_file.write(missing_values.to_string())
output_file.write("\n")

# Close the output file
output_file.close()
