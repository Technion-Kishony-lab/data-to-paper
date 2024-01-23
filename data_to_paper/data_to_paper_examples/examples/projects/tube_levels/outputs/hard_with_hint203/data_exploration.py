
import pandas as pd

# Load data
data = pd.read_csv("tracheal_tube_insertion.csv")

# Open output file
with open("data_exploration.txt", "w") as file:

    # Write size of the data
    file.write("# Data Size\n")
    file.write(f"Number of rows: {data.shape[0]}\n")
    file.write(f"Number of columns: {data.shape[1]}\n\n")

    # Write summary statistics
    file.write("# Summary Statistics\n")
    file.write(data.describe().to_string())
    file.write("\n\n")

    # Write categorical variables
    file.write("# Categorical Variables\n")
    file.write(data['sex'].value_counts().to_string())
    file.write("\n\n")

    # Count missing values
    file.write("# Missing Values\n")
    missing_values = data.isnull().sum()
    file.write(missing_values.to_string())
    file.write("\n")

# Close output file   
