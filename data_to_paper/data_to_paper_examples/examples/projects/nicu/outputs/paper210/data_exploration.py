
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# DataFrame shape
num_rows = df.shape[0]
num_columns = df.shape[1]

# Categorical Variables - First find out categorical variables, then list their mode and unique counts
df_cat = df.select_dtypes(include=['object'])
cat_dict = {}
for col in df_cat.columns:
    mode = df_cat[col].mode()[0]
    unique_count = df_cat[col].nunique()
    cat_dict[col] = (mode, unique_count)

# Missing Values - Count of nulls in each column
missing_values = df.isnull().sum()
missing_values = missing_values[missing_values > 0]

# Open file and write the results
with open("data_exploration.txt", "w") as f:
    
    # Write Data Size
    f.write(f"# Data Size\nNumber of rows: {num_rows}\nNumber of columns: {num_columns}\n")
    
    # Write Summary Statistics
    f.write("\n# Summary Statistics\n")
    for col in df.columns:
        if np.issubdtype(df[col].dtype, np.number):
            mean = df[col].mean()   # Mean for numeric columns
            std = df[col].std()     # Standard deviation for numeric columns
            f.write(f"\n{col}:\nMean: {mean}\nStd: {std}\n")
        
    # Write Categorical Variables
    f.write("\n# Categorical Variables\n")
    for cat, stats in cat_dict.items():
        f.write(f"\n{cat}:\nMode: {stats[0]}\nNumber of unique values: {stats[1]}\n")

    # Write Missing Values
    f.write("\n# Missing Values\n")
    if missing_values.empty:
        f.write("No missing values\n")
    else:
        for col, num in missing_values.items():
            f.write(f"{col}: {num}\n")
        
    # Write dataset summary
    f.write("\n# Data Summary\nThis dataset represents deliveries pre and post implementation of new guidelines introduced in 2015 with respect to Neonatal Resuscitation Program (NRP). It contains clinical information on the mother and newborn, along with treatments and outcomes.")

