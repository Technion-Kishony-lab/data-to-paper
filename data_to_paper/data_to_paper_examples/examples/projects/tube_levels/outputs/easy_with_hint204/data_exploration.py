
import pandas as pd

# Load the CSV data into a DataFrame
df = pd.read_csv('tracheal_tube_insertion.csv')

# Create a text file and write data exploration summary into it
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write("# Data Size\n")
    f.write(f"Number of rows: {df.shape[0]}\n")
    f.write(f"Number of columns: {df.shape[1]}\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    desc = df.describe(include='all')
    for col in desc.columns:
        f.write(f"{col}\n{desc[col]}\n\n")

    # Categorical Variables
    f.write("# Categorical Variables\n")
    categorical_cols = df.select_dtypes(include=['object','bool']).columns
    for col in categorical_cols:
        f.write(f"{col} - most common values:\n{df[col].value_counts().head().to_string()}\n\n")

    # Missing Values
    f.write("# Missing Values\n")
    missing_vals = df.isnull().sum()
    for key, val in missing_vals.items():
        if val > 0:
            f.write(f"{key}: {val} missing values\n")
            
    # Addition could be done here for exploring other data metrics
