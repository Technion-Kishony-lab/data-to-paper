
import pandas as pd
import numpy as np
from collections import Counter

# Load data
data = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# Output file
output_file = open("data_exploration.txt", "w")

# Data Size
output_file.write("# Data Size\n")
output_file.write(f"Number of Rows: {data.shape[0]}\n")
output_file.write(f"Number of Columns: {data.shape[1]}\n\n")

# Summary Statistics
output_file.write("# Summary Statistics\n")
summary_statistics = data.describe(include='all')
output_file.write(f"{summary_statistics}\n\n")

# Categorical Variables
output_file.write("# Categorical Variables\n")
categorical_cols = data.select_dtypes(include=['object']).columns
for col in categorical_cols:
    output_file.write(f"{col}: {dict(Counter(data[col]))}\n")
output_file.write("\n")

# Missing Values
output_file.write("# Missing Values\n")
missing_values = data.isnull().sum()
output_file.write(f"{missing_values}\n\n")

output_file.close()
