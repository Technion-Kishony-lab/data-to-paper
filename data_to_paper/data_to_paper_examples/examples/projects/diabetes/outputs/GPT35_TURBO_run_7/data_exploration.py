
import pandas as pd
import numpy as np

# Read the data file
data = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Create a text file for output
output_file = open('data_exploration.txt', 'w')

# Data Size
output_file.write('# Data Size\n')
output_file.write('Number of rows: {}\n'.format(len(data)))
output_file.write('Number of columns: {}\n\n'.format(len(data.columns)))

# Summary Statistics
output_file.write('# Summary Statistics\n')
output_file.write('Summary statistics of all variables:\n')
output_file.write('{}\n\n'.format(data.describe()))

# Categorical Variables
output_file.write('# Categorical Variables\n')
categorical_variables = ['Diabetes_binary', 'HighBP', 'HighChol', 'CholCheck', 
                         'Smoker', 'Stroke', 'HeartDiseaseorAttack', 'PhysActivity', 
                         'Fruits', 'Veggies', 'HvyAlcoholConsump', 'AnyHealthcare', 
                         'NoDocbcCost', 'GenHlth', 'DiffWalk', 'Sex', 'Age', 'Education', 'Income']

output_file.write('Most common values for each categorical variable:\n')
for variable in categorical_variables:
    output_file.write('Variable: {}\n'.format(variable))
    output_file.write('{}\n'.format(data[variable].value_counts()))
    output_file.write('\n')

# Missing Values
output_file.write('# Missing Values\n')
output_file.write('Counts of missing values:\n')
output_file.write('{}\n'.format(data.isnull().sum()))

# Close the output file
output_file.close()
