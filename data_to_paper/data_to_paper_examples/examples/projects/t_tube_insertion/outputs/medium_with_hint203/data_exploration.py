
import pandas as pd

# Load the data from a CSV file into a pandas data frame
df = pd.read_csv("tracheal_tube_insertion.csv")

# Open a new text file to output our data exploration
with open("data_exploration.txt", "w") as f:
    
    # Data Size
    f.write("# Data Size\n")
    f.write(f"Number of rows: {df.shape[0]}\n")
    f.write(f"Number of columns: {df.shape[1]}\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    f.write(df.describe().to_string())
    f.write("\n\n")

    # Categorical Variables
    f.write("# Categorical Variables\n")
    cat_vars = df.select_dtypes(include=['object']).columns
    for col in cat_vars:
        f.write(f"For variable {col}, the most common value is {df[col].mode()[0]}\n")
    f.write("\n")

    # Missing Values
    f.write("# Missing Values\n")
    missing_data = df.isnull().sum()
    missing_cols = missing_data[missing_data > 0]
    if missing_cols.empty:
        f.write("Dataset has no missing values.\n")
    else:
        for col in missing_cols.index:
            f.write(f"Variable {col} has {missing_cols[col]} missing values.\n")

# If necessary, additional summary of the data could be added to the above code
