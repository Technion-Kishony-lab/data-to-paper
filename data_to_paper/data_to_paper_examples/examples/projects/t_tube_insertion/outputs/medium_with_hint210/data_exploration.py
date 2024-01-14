
import pandas as pd

# Load data
data = pd.read_csv("tracheal_tube_insertion.csv")

# Open output file
with open("data_exploration.txt", "w") as file:

    # Data size
    file.write("# Data Size\n")
    file.write(f'Number of rows: {data.shape[0]}\n')
    file.write(f'Number of columns: {data.shape[1]}\n')

    # Summary Statistics
    file.write("\n# Summary Statistics\n")
    file.write(str(data.describe()))

    # Categorical Variables
    file.write("\n# Categorical Variables\n")
    categorical_columns = data.select_dtypes(include=['object', 'bool']).columns
    if len(categorical_columns) > 0:
        for col in categorical_columns:
            file.write(f'{col} most common: {data[col].mode()[0]}\n')
    else:
        file.write('No categorical variables\n')

    # Missing Values
    file.write("\n# Missing Values\n")
    file.write(str(data.isna().sum()))

    # Other summary that may be:
    file.write("\n# Values count for 'sex' column\n")
    file.write(str(data.sex.value_counts()))
