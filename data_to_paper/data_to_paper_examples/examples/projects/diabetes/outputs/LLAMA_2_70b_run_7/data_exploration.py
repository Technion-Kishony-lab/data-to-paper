
import pandas as pd
import numpy as np
from scipy import stats

# Load the data from the CSV file
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Create the output file
with open("data_exploration.txt", "w") as f:
    # Write the column names
    f.write(str(df.columns) + "\n")
    
    # Write the data size
    f.write("# Data Size: \t" + str(len(df)) + "\n")
    
    # Write the summary statistics
    f.write("# Summary Statistics\n")
    stats_dict = df.describe()
    for var in ["mean", "std", "min", "max"]:
        if var in df.columns:
            f.write(f"{var}: {stats_dict[var]} (n={len(df)})")
            f.write("\n")
        else:
            f.write(f"{var}: --NotFound--")
            f.write("\n")
    
    # Write the categorical variables
    f.write("# Categorical Variables\n")
    categorical_vars = ["Sex", "Age", "Education", "Income"]
    for var in categorical_vars:
        f.write(f"{var}:\n")
        f.write(pd.value_counts(df[var]).head().to_string() + "\n")
    
    # Write the missing values
    f.write("# Missing Values\n")
    missing_values = df.isnull().sum()
    f.write(f"Missing value count: {missing_values}\n")
    if df['Diabetes_binary'].isnull().any():
        f.write(f"Special numeric value for missing Diabetes status: {df['Diabetes_binary'].isnull().unique()}")
        f.write("\n")
    
    # Write the range of BMI
    f.write("\n# Range of BMI\n")
    bmi_range = df["BMI"].dropna().tolist()
    f.write(f"Minimum BMI: {np.min(bmi_range)}\n")
    f.write(f"Maximum BMI: {np.max(bmi_range)}\n")
    
    # Write the percentage with high blood pressure
    f.write("\n# Percentage with High Blood Pressure\n")
    high_bp = df["HighBP"].value_counts()[1] / len(df) * 100
    f.write(f"Percentage with high blood pressure: {round(high_bp, 2)}%\n")

# Close the output file
f.close()
