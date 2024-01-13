
import pandas as pd

# Load data
df = pd.read_csv("tracheal_tube_insertion.csv")

with open("data_exploration.txt", "w") as file:
    # Measure the scale of our data
    file.write("# Data Size\n")
    file.write(f"Number of rows: {df.shape[0]}\n")
    file.write(f"Number of columns: {df.shape[1]}\n\n")

    # Summary statistics of all key variables
    file.write("# Summary Statistics\n")
    desc = df.describe(include="all")
    file.write(f"{desc}\n\n")
    
    # Categorical Variables
    cat_cols = df.select_dtypes(include=['object']).columns
    file.write("# Categorical Variables\n")
    for col in cat_cols:
        most_common = df[col].value_counts().idxmax()
        file.write(f"{col}: {most_common}\n")
    file.write("\n")
    
    # Missing values
    file.write("# Missing Values\n")
    missing_val_counts = df.isnull().sum()
    file.write(f"{missing_val_counts}\n")
    
    # Special numeric values
    # No specific information in the dataset description, so skip for now
