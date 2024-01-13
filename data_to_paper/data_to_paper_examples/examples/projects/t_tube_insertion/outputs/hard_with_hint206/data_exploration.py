

# Import pandas library
import pandas as pd

# Read the dataset
data = pd.read_csv("tracheal_tube_insertion.csv")

# Opens a output text file and writes the exploration data
with open("data_exploration.txt", "w") as f:

    # Data Size
    f.write("# Data Size\n")
    f.write("Number of rows in the dataset: {}\n".format(len(data.index)))
    f.write("Number of columns in the dataset: {}\n".format(len(data.columns)))

    # Summary Statistics
    f.write("\n# Summary Statistics\n")
    summary_stats = data.describe().transpose()
    f.write(str(summary_stats))
    f.write('\n\n')

    # Categorical Variables
    f.write("\n# Categorical Variables\n")
    categorical = data.select_dtypes(include=['object'])
    if not categorical.empty:
        f.write('Categorical features in the Dataset are:\n')
        f.write(str(categorical.columns.tolist()))
        f.write('\n\nCounts of unique values in each categorical variable:\n')
        for col in categorical.columns:
            f.write(str(data[col].value_counts()))
    else:
        f.write("The dataset does not contain any categorical column.\n")

    # Missing Values
    f.write("\n# Missing Values\n")
    missing_values = data.isnull().sum()
    f.write("Counts of missing, null or undefined values per column:\n")
    for ind, val in missing_values.items():    # Changed from iteritems (which is not valid for Series) to items
        f.write("{}: {}\n".format(ind, val))

