
import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# Separate numeric and non-numeric columns
numeric = df._get_numeric_data()
non_numeric = df.select_dtypes(include=[object])

# Handling missing values
numeric.fillna(numeric.mean(), inplace=True)
non_numeric.fillna(non_numeric.mode().iloc[0], inplace=True)

# Combine numeric and non-numeric dataframes
df = pd.concat([numeric, non_numeric], axis=1)

# Start writing to the output file
with open("data_exploration.txt", "w") as output_file:
    
    # General Summary
    output_file.write("# General Summary\n")
    output_file.write("This dataset contains information about Neonatal Resuscitation Program (NRP) guidelines. It compares Pre-2015 and Post-2015 policies involving treatments for 223 newborns.\n\n")
    
    # Data Size
    output_file.write("# Data Size\n")
    output_file.write("The dataset contains {} rows (representing 223 deliveries) and {} columns (representing the newborns' various characteristics and treatments received).\n\n".format(df.shape[0], df.shape[1]))
    
    # Summary Statistics
    output_file.write("# Summary Statistics\n")
    output_file.write("Summary statistics provide an initial insight into the dataset. They include count, mean, standard deviation (std), minimum (min), 25th percentile (25%), median (50%), 75th percentile (75%), and maximum (max) values for each numerical column in the dataset. Below are the summary statistics for numerical variables:\n")
    output_file.write(str(df.describe()) + "\n\n")
    
    # Categorical Variables Summary
    output_file.write("# Categorical Variables\n")
    output_file.write("Categorical variables are non-numerical data such as characters or categories. Below is a count of unique values, with the most frequent category, for each categorical variable:\n")
    categorical_columns = df.select_dtypes(include=['object']).columns
    for column in categorical_columns:
        output_file.write("Variable '{}': {} unique values, most common category is '{}'\n".format(column, df[column].nunique(), df[column].mode().iloc[0]))
    output_file.write("\n")
    
    # Missing Values
    output_file.write("# Missing Values\n")
    output_file.write("Missing values were filled with the mean (for numerical variables) or mode (for categorical variables). Thus, there are now 0 missing values in the dataset. Below is the updated count for confirmation:\n")
    missing_values = df.isnull().sum()
    for column in df.columns:
        output_file.write("For '{}', Number of Missing values: {}\n".format(column, missing_values[column]))
    output_file.write("\n")
