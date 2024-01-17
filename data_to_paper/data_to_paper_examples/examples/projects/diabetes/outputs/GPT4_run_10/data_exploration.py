
import pandas as pd
import numpy as np

# Read the data from the csv file
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Open a new file to write the data summary
with open('data_exploration.txt', 'w') as file:
    # Write the size of the data
    file.write("# Data Size\n")
    file.write("Number of Rows: " + str(df.shape[0]) + "\n")
    file.write("Number of Columns: " + str(df.shape[1]) + "\n\n")

    # Write the summary statistics of the data
    file.write("# Summary Statistics\n")
    summary = df.describe(include='all')
    file.write(str(summary) + "\n\n")

    # Write the categorical variables and their most common values
    file.write("# Categorical Variables\n")
    categorical_variables = df.select_dtypes(include=['object']).columns
    for variable in categorical_variables:
        file.write("Variable: " + variable + "\n")
        file.write("Most Common Value: " + df[variable].mode()[0] + "\n")
    file.write("\n")

    # Write the count of missing values
    # Since there are no missing values according to dataset description, this count should be 0. 
    file.write("# Missing Values\n")
    file.write("Total Missing Values: " + str(df.isnull().sum().sum()) + "\n\n")

    # As per dataset description, there are no special numeric values for unknown or undefined
    
    file.close()
