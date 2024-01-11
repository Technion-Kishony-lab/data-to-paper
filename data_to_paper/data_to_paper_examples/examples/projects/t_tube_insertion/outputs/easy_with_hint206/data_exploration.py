
import pandas as pd

# Load the data
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open the output file
with open("data_exploration.txt", "w") as f:

    # Write the header
    f.write("# Data Size\n")
    
    # Write data size
    rows, cols = df.shape
    f.write(f"Number of Rows: {rows}\n")
    f.write(f"Number of Columns: {cols}\n")

    # Write the header for the summary statistics
    f.write("\n# Summary Statistics\n")

    # Calculate and write summary statistics
    summary_stat = df.describe()
    f.write(f"{summary_stat}\n")

    # Write the header for categorical variables
    f.write("\n# Categorical Variables\n")

    # Identify categorical variables and write most common values
    categorical_var = df.select_dtypes(include=['object']).columns.tolist()
    for var in categorical_var:
        f.write(f"Most common values for {var}:\n")
        f.write(f"{df[var].value_counts().head()}\n")

    # Write the header for missing values
    f.write("\n# Missing Values\n")

    # Identify and write counts of missing, unknown, or undefined values
    missing_values = df.isnull().sum()
    f.write(f"{missing_values}\n")
