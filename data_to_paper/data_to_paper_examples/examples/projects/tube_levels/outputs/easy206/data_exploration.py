

import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv("tracheal_tube_insertion.csv")

# Open output file
out_file = open("data_exploration.txt", "w")

# Data size
out_file.write("# Data Size\n")
out_file.write("Number of Rows: {}\n".format(df.shape[0]))
out_file.write("Number of Columns: {}\n\n".format(df.shape[1]))

# Summary Statistics
out_file.write("# Summary Statistics\n")
out_file.write(df.describe().to_string())
out_file.write("\n\n")

# Categorical Variables
out_file.write("# Categorical Variables\n")
out_file.write(df['sex'].value_counts().to_string())
out_file.write("\n\n")

# Missing Values
out_file.write("# Missing Values\n")
out_file.write(df.isnull().sum().to_string())
out_file.write("\n\n")

# Close output file
out_file.close()

