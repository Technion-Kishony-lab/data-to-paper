
import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# Categorical and Numerical Columns
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(include=['object']).columns.tolist()

# Open a file for writing
summary_file = open("data_exploration.txt", "w")

# Write Data Size to the file
summary_file.write("# Data Size\n")
summary_file.write(f'Rows: {df.shape[0]}, Columns: {df.shape[1]}\n\n')

# Special number checks and filling missing values in numeric data
summary_file.write("# Special numeric values check\n")
for col in num_cols:
    special_values = df[(df[col] == -999) | (df[col] == 999)]
    if not special_values.empty:
        summary_file.write(f'\n{col}: \n')
        summary_file.write(special_values.to_string())
        summary_file.write('\n')
    df[col].replace([-999, 999], df[col].median(), inplace=True)
    df[col].fillna(df[col].median(), inplace=True)

# Special categories checks and filling missing values in categorical data
summary_file.write("\n\n# Special categorical values check\n")
for col in cat_cols:
    special_values = df[(df[col] == 'undefined') | (df[col] == 'unknown')]
    if not special_values.empty:
        summary_file.write(f'\n{col}: \n')
        summary_file.write(special_values.to_string())
        summary_file.write('\n')
    df[col].replace(['undefined', 'unknown'], df[col].mode()[0], inplace=True)
    df[col].fillna(df[col].mode()[0], inplace=True)

# Write Summary Statistics
summary_file.write("\n# Summary Statistics\n")
summary_file.write(df.describe().to_string())
summary_file.write('\n\n')

# Write Categorical Variables
summary_file.write("\n# Categorical Variables\n")
for col in cat_cols:
    summary_file.write(f'\n{col}: \n')
    summary_file.write(df[col].value_counts().to_string())
    summary_file.write(f'\nUnique values: {df[col].nunique()}\n')

# Check for Missing Values
summary_file.write("\n\n# Missing Values\n")
missing_values = df.isnull().sum()
summary_file.write(missing_values[missing_values > 0].to_string())
summary_file.write('\n')

# Write a summary of the distribution of the target variable 'PrePost'
summary_file.write("\n# Distribution of the Target Variable 'PrePost'\n")
summary_file.write(df['PrePost'].value_counts().to_string())
summary_file.write('\n')

# Update numerical data setting correlations just for them
df_num = df.select_dtypes(include=[np.number])

# Write a summary of the correlation between the features and the target variable
summary_file.write("\n# Correlation between the Features and the Target Variable\n")
correlations = df_num.corr()['PrePost'].sort_values()
summary_file.write(correlations.to_string())

# Close the file
summary_file.close()
