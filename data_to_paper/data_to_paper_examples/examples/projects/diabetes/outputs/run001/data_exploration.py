

import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Open the output text file
with open("data_exploration.txt", "w") as f:

  # Print the size of the Data
  f.write("# Data Size\n")
  f.write(f"Number of Rows: {df.shape[0]}\n")
  f.write(f"Number of Columns: {df.shape[1]}\n\n")

  # Print summary statistics
  f.write("# Summary Statistics\n")
  summary_stats = df.describe(include='all').transpose()
  f.write(f"{summary_stats}\n\n")

  # Identify & count the categorical variables
  f.write("# Categorical Variables\n")
  categorical_columns = df.select_dtypes(include=['bool', 'object']).columns
  if len(categorical_columns) == 0:
    f.write("Not applicable\n\n")
  else:
    categorical_variable_stats = df[categorical_columns].describe().transpose()
    f.write(f"{categorical_variable_stats}\n\n")

  # Print counts of missing/undefined values
  f.write("# Missing Values\n")
  missing_values = df.isnull().sum().to_frame(name='Missing values count')
  if missing_values.empty:
    f.write("Not applicable\n\n")
  else:
    f.write(f"{missing_values}\n\n")

  # Anything else you deem relevant. 
  # For example, you might want to count each classes in Diabetes_binary
  f.write("# Count of classes in Diabetes_binary\n")
  diabetes_binary_counts = df['Diabetes_binary'].value_counts().to_frame(name='Counts')
  f.write(f"{diabetes_binary_counts}\n\n")

f.close()

