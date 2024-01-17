
import pandas as pd

# Read the dataset
data = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Create an empty list to store the summary information
summary = []

# Append the data size summary
summary.append("# Data Size")
summary.append("Number of rows: {}".format(data.shape[0]))
summary.append("Number of columns: {}".format(data.shape[1]))

# Append the summary statistics
summary.append("\n# Summary Statistics")
summary.append(data.describe().to_string())

# Append the categorical variables and their most common values
summary.append("\n# Categorical Variables")
categorical_vars = ['Diabetes_binary', 'HighBP', 'HighChol', 'CholCheck', 'Smoker', 'Stroke',
                    'HeartDiseaseorAttack', 'PhysActivity', 'Fruits', 'Veggies', 'HvyAlcoholConsump',
                    'AnyHealthcare', 'NoDocbcCost', 'GenHlth', 'DiffWalk', 'Sex', 'Age', 'Education', 'Income']
for var in categorical_vars:
    summary.append("\n{}:".format(var))
    summary.append(data[var].value_counts().head().to_string())

# Append the missing values summary
summary.append("\n# Missing Values")
summary.append(data.isnull().sum().to_string())

# Save the summary to the output file
with open("data_exploration.txt", "w") as file:
    summary_text = '\n'.join(summary)
    file.write(summary_text)
