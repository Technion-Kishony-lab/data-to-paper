
import pandas as pd

# Load the csv data
file_path = 'tracheal_tube_insertion.csv'
data = pd.read_csv(file_path)

# Open the file to write output
with open("data_exploration.txt", "w") as out_file:

    # Data Size
    out_file.write("# Data Size\n")
    nrows, ncols = data.shape
    out_file.write(f"Number of rows: {nrows}, Number of columns: {ncols}\n\n")

    # Summary Statistics
    out_file.write("# Summary Statistics\n")
    summary = data.describe(include='all')
    out_file.write(f"{summary}\n\n")

    # Categorical Variables
    out_file.write("# Categorical Variables\n")
    categorical_columns = data.select_dtypes(include=['object']).columns
    for column in categorical_columns:
        most_common = data[column].value_counts().idxmax()
        out_file.write(f"For column {column}, most common value is: {most_common}\n")
    out_file.write("\n")

    # Missing Values
    out_file.write("# Missing Values\n")
    count_missing = data.isna().sum()
    out_file.write(f"{count_missing}\n")
    out_file.write("\n")

    # look for -1 / -999 / other stated in the description special numeric values that express missing value
    out_file.write("# Special Numeric Values Interpreted as Missing\n")
    special_values = [-1, -999] # replace with the list of the special values, as needed
    for value in special_values:
        count_special = (data == value).sum()
        out_file.write(f"For the special value of {value} as missing, counts are:\n{count_special}\n")
    out_file.write("\n")
