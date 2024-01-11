
# Import the required libraries
import pandas as pd

# Load the data
df = pd.read_csv('tracheal_tube_insertion.csv', header=0)

# Open file for writing results
with open("data_exploration.txt", "w") as file:
    
    # Data Size
    file.write("# Data Size\n")
    file.write("Number of Rows: " + str(df.shape[0]) + "\n")
    file.write("Number of Columns: " + str(df.shape[1]) + "\n\n")

    # Summary Statistics
    file.write("# Summary Statistics\n")
    summary_stats = df.describe(include='all')
    file.write(str(summary_stats) + "\n\n")

    # Categorical Variables
    file.write("# Categorical Variables\n")
    for column in df.columns:
        if df[column].dtype == "object":
            file.write("\nColumn name: " + column + "\n")
            file.write("Most common values:\n")
            file.write(str(df[column].value_counts().nlargest(5)) + "\n\n")

    # Missing Values
    file.write("# Missing Values\n")
    file.write("Null value counts:\n")
    file.write(str(df.isna().sum()) + "\n\n")

    # Check if numeric columns have special undefined values.
    special_vals = [-99, -999, -9999]
    for val in special_vals:
        for column in df.select_dtypes(include=['float64', 'int64']).columns:
            if (df[column] == val).any():
                file.write("Column '" + column + "' has special numeric value (" + str(val) + ") representing unknown/undefined.\n")
                
file.close()
