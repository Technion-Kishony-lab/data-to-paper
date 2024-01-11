
import pandas as pd

# Load the data
dataset = pd.read_csv('tracheal_tube_insertion.csv')

# Open the output file
with open("data_exploration.txt", "w") as file:

    # Data size
    file.write("# Data Size\n")
    file.write(f"Number of rows: {dataset.shape[0]}\n")
    file.write(f"Number of columns: {dataset.shape[1]}\n\n")

    # Summary Statistics
    file.write("# Summary Statistics\n")
    stats = dataset.describe(include='all')
    file.write(str(stats) + '\n\n')

    # Categorical Variables
    file.write("# Categorical Variables\n")
    categorical_cols = dataset.select_dtypes(['object','bool']).columns
    for col in categorical_cols:
        file.write(f"{col} most common values:\n")
        file.write(str(dataset[col].value_counts().head()) + "\n\n")

    # Missing values
    file.write("# Missing Values\n")
    missing_vals = dataset.isnull().sum()
    file.write(str(missing_vals) + "\n")
    
    # use replace to count special numeric values that stand for unknown/undefined if any
    # For the current dataset, it does not seem to apply.
