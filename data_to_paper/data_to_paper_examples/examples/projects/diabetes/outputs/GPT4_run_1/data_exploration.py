
import pandas as pd

# Load the dataset
data = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Open output file
with open("data_exploration.txt", "w") as f:

    # Write data size
    f.write("# Data Size\n")
    f.write(f"Number of Rows: {data.shape[0]}\n")
    f.write(f"Number of Columns: {data.shape[1]}\n\n")

    # Write summary statistics
    f.write("# Summary Statistics\n")
    # Select numerical columns only
    numerical_columns = data.select_dtypes(include=['int64', 'float64']).columns
    # Write summary statistics of these columns
    for col in numerical_columns:
        f.write(f"{data[col].describe()}\n\n")

    # Write categorical variables
    f.write("# Categorical Variables\n")
    # Select categorical columns only
    categorical_columns = data.select_dtypes(include=['object']).columns
    # Write unique categories and most common value of these columns
    for col in categorical_columns:
        f.write(f"{col} Unique Categories: {data[col].unique()}\n")
        f.write(f"Most Common Value: {data[col].mode().values[0]}\n\n")

    # Write missing values
    f.write("# Missing Values\n")
    # Write counts of missing values for each column
    for col in data.columns:
        f.write(f"{col} Missing Value Count: {data[col].isnull().sum()}\n")
    f.write("\nNote: all missing values were already removed from the original data.\n")
