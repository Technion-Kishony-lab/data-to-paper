
import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Creating an output file
file = open("data_exploration.txt","w") 

# Data Size
file.write("# Data Size\n")
file.write("Number of records: {}\n".format(df.shape[0]))
file.write("Number of features: {}\n\n".format(df.shape[1]))

# Summary Statistics
file.write("# Summary Statistics\n")
for col in df.columns:
    file.write("\nSummary Statistics for feature '{}':\n".format(col))
    file.write(str(df[col].describe()) + "\n")

# Categorical Variables
file.write("\n# Categorical Variables\n")
categorical_columns = df.select_dtypes(include = ['bool', 'object']).columns.tolist()
for categorical_column in categorical_columns:
    file.write("\nCategorical variable '{}':\n".format(categorical_column))
    file.write(str(df[categorical_column].value_counts().head().to_string()) + "\n")

# Missing values
file.write("\n# Missing Values\n")
file.write('Total missing values in the dataset: {}\n'.format(df.isnull().sum().sum()))
missing_values_per_column = df.isnull().sum().to_string()
file.write("{}\n".format(missing_values_per_column))

file.close()

