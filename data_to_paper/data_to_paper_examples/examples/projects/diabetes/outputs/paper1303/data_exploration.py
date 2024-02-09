

import pandas as pd

# Loading the dataset
data = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Creating the output file
with open("data_exploration.txt", 'w') as f:

    f.write("# Data Size\n")
    f.write("Number of Rows: " + str(data.shape[0]) + "\n")
    f.write("Number of Columns: " + str(data.shape[1]) + "\n\n")

    f.write("# Summary Statistics\n")
    summary_stats = data.describe()
    f.write("For each variable, we have:\n")
    for var in summary_stats.columns:
        f.write(f"{var}: Mean = {summary_stats[var]['mean']:.2f}, Std Dev = {summary_stats[var]['std']:.2f}, "
                f"Min = {summary_stats[var]['min']}, Q1 = {summary_stats[var]['25%']}, Median = {summary_stats[var]['50%']}, "
                f"Q3 = {summary_stats[var]['75%']}, Max = {summary_stats[var]['max']}\n")

    f.write("\n# Categorical Variables\n")
    for col in data.columns:
        if data[col].dtype == "object" or len(data[col].unique()) <= 5:
            f.write(f"{col}: {data[col].mode().values[0]} is the most common value\n")

    f.write("\n# Missing Values\n")
    if not data.isnull().values.any():
        f.write("There are no missing values in the dataset.\n\n")
    else:
        f.write(data.isnull().sum().to_string())
        f.write("\n\n")

f.close()

