
import pandas as pd
import numpy as np

# Load the csv data into a data frame
df_tracheal_tube = pd.read_csv("tracheal_tube_insertion.csv")

# Start writing the 'data_exploration.txt' file
with open('data_exploration.txt', 'w') as f:

    # Data size
    f.write("# Data Size\n")
    f.write(f"Number of Rows: {df_tracheal_tube.shape[0]}\n")
    f.write(f"Number of Columns: {df_tracheal_tube.shape[1]}\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    summary_stats = df_tracheal_tube.describe(include=[np.number]).transpose().to_string()
    f.write(f"{summary_stats}\n\n")

    # Categorical Variables
    f.write("# Categorical Variables\n")
    # Assuming 'sex' as the only categorical variable in this case
    male_count = df_tracheal_tube['sex'].value_counts()[1]
    female_count = df_tracheal_tube['sex'].value_counts()[0]
    f.write(f"Sex: Male count = {male_count}, Female count = {female_count}\n\n")

    # Missing Values
    f.write("# Missing Values\n")
    missing_values = df_tracheal_tube.isnull().sum().to_string()
    f.write(f"{missing_values}\n\n")

    # Since the dataset description does not provide indication of special cases of numeric values standing in for unknown or undefined values, this section is not added to the code.
