
import pandas as pd

# Read the data from the CSV file
data = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Create an empty dictionary to store the summary statistics
summary_stats = {}

# Add the measure of scale of the data to the summary_stats dictionary
summary_stats['Data Size'] = f"{data.shape[0]} rows, {data.shape[1]} columns"

# Add the summary statistics of all variables to the summary_stats dictionary
summary_stats['Summary Statistics'] = data.describe().to_string()

# Calculate the most common values for categorical variables
categorical_vars = ['Diabetes_binary', 'HighBP', 'HighChol', 'CholCheck', 'Smoker', 'Stroke',
                    'HeartDiseaseorAttack', 'PhysActivity', 'Fruits', 'Veggies', 'HvyAlcoholConsump',
                    'AnyHealthcare', 'NoDocbcCost', 'GenHlth', 'DiffWalk', 'Sex', 'Age', 'Education', 'Income']
most_common_values = {}
for var in categorical_vars:
    most_common_values[var] = data[var].value_counts().idxmax()

# Add the categorical variables and their most common values to the summary_stats dictionary
summary_stats['Categorical Variables'] = str(most_common_values)

# Calculate counts of missing, unknown, or undefined values
missing_counts = data.isnull().sum().to_frame('Missing Values')

# Calculate counts of special numeric values that stand for unknown/undefined if any
special_values = {}
special_numeric_values = {'Diabetes_binary': [9], 'HighBP': [9], 'HighChol': [9], 'CholCheck': [9],
                          'Smoker': [9], 'Stroke': [9], 'HeartDiseaseorAttack': [9], 'PhysActivity': [9],
                          'Fruits': [9], 'Veggies': [9], 'HvyAlcoholConsump': [9], 'AnyHealthcare': [9],
                          'NoDocbcCost': [9], 'GenHlth': [7], 'DiffWalk': [9, 7]}
for var, values in special_numeric_values.items():
    special_values[var] = sum(data[var].isin(values))

# Combine missing counts and special values into a single dataframe
missing_values_df = pd.concat([missing_counts, pd.DataFrame(special_values, index=['Special Values'])])

# Add the missing values and special values to the summary_stats dictionary
summary_stats['Missing Values'] = missing_values_df.to_string()

# Write the summary_stats dictionary to the output file
with open('data_exploration.txt', 'w') as file:
    for section, content in summary_stats.items():
        file.write(f"# {section}\n{content}\n\n")
