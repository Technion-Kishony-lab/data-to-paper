
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('meconium_nicu_dataset_preprocessed_short.csv')

# Open output file
with open('data_exploration.txt', 'w') as f:
    # Data size section
    f.write("# Data Size\n")
    f.write("Number of rows: {}\n".format(df.shape[0]))
    f.write("Number of columns: {}\n".format(df.shape[1]))
    
    # Summary Statistics section
    f.write("\n# Summary Statistics\n")
    summary_stats = df[['AGE', 'BirthWeight', 'GestationalAge', 'LengthStay']].describe() # only key variables
    f.write(summary_stats.to_string() + "\n")

    # Categorical Variables section
    f.write("\n# Categorical Variables\n")
    categorical_columns = df.select_dtypes(include=['object']).columns
    for column in categorical_columns:
        f.write("Column Name: {}\n".format(column))
        f.write("Most common values:\n")
        f.write(df[column].value_counts().head(5).to_string() + "\n\n") # only top 5
        
    # Missing Values section
    f.write("\n# Missing Values\n")
    total_missing_values = df.isnull().sum().sum()
    f.write("Total missing values in the dataset: {}\n".format(total_missing_values))

    # Check for special numeric values section
    f.write("\n# Special Numeric Values\n")
    zero_values = (df == 0).astype(int).sum()
    zero_value_columns = zero_values[zero_values > 0].index.tolist()
    if zero_value_columns:
        f.write("Columns with 0s (may signify missing data):\n")
        for column in zero_value_columns:
            f.write("Column {}: {}\n\n".format(column, zero_values[column]))
    else:
        f.write("No columns with special numeric values.\n")

    # Extra summary: correlation among key variables 
    f.write("\n# Extra Summary: Pearson Correlation Among Key Numerical Variables\n")
    numerical_corr = df[['AGE', 'BirthWeight', 'GestationalAge', 'LengthStay']].corr() # only key variables
    f.write(numerical_corr.to_string() + "\n")
