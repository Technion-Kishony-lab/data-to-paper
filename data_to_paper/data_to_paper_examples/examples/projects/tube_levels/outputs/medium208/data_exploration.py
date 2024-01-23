
import pandas as pd
import numpy as np

# load the dataset
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open file for writing the exploration results
with open("data_exploration.txt", "w") as f:

    # Check the size of our data
    f.write("# Data Size\n")
    f.write(str(df.shape) + "\n\n")

    # Summary statistics of all or key variables
    f.write("# Summary Statistics\n")
    f.write(str(df.describe()) + "\n\n")

    # Categorical Variables
    f.write("# Categorical Variables\n")
    f.write(str(df['sex'].value_counts()) + "\n\n")

    # missing and special values
    f.write("# Missing Values\n")
    f.write(str(df.isnull().sum()) + "\n\n")
