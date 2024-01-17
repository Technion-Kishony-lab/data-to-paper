
import pandas as pd
import numpy as np
import scipy

# Load the data
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Open the output file
with open("data_exploration.txt", "w") as f:
    # Write the header
    f.write("# Data Size\n")
    f.write(f"Number of rows: {len(df)}\n")
    f.write(f"Number of columns: {df.shape[1]}\n")

    # Summary statistics
    f.write("\n# Summary Statistics\n")
    for column in df.drop(columns=["Diabetes_binary"]):
        mean = df[column].mean()
        std = df[column].std()
        f.write(f"{column}: {mean} (+/- {std})\n")

    # Categorical variables
    f.write("\n# Categorical Variables\n")
    categorical_variables = ["Sex", "Education", "Income"]
    for variable in categorical_variables:
        f.write(f"{variable}: \n")
        f.write(f"Value count: {df[variable].value_counts().index[0]} \n")
        f.write(f"Mode: {df[variable].mode()[0]} \n")

    # Missing values
    f.write("\n# Missing Values\n")
    missing_values = df.isna().sum()
    if missing_values.any():
        f.write(f"Missing values found: {missing_values.tolist()}\n")
    else:
        f.write("No missing values found.\n")

    # Other summaries
    f.write("\n# Other Summaries\n")
    unique_ages = df["Age"].unique()
    f.write(f"Unique ages: {len(unique_ages)} \n")
    average_bmi = df["BMI"].mean()
    f.write(f"Average BMI: {average_bmi} \n")
