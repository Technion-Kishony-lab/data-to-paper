
import pandas as pd
import numpy as np

# load the data
df = pd.read_csv('tracheal_tube_insertion.csv')

with open('data_exploration.txt', 'w') as file:
    # Data Size
    file.write("# Data Size\n")
    file.write(f"Number of rows: {df.shape[0]}\n")
    file.write(f"Number of columns: {df.shape[1]}\n\n")

    # Summary Statistics
    file.write("# Summary Statistics\n")
    descr = df.describe(include='all')
    file.write(f"{descr}\n\n")

    # Categorical Variables
    file.write("# Categorical Variables\n")
    cat_cols = df.select_dtypes(include=['object', 'bool'])
    for col in cat_cols.columns:
        top_freq = df[col].value_counts().idxmax()
        file.write(f"{col}: Most frequent is {top_freq}\n")
    file.write("\n")

    # Missing Values
    file.write("# Missing Values\n")
    missing = df.isnull().sum()
    file.write(f"{missing}\n\n") # general missing values

    # check for special numeric values that might indicate missing/unknown
    special_numeric = (df < 0).sum()      
    file.write(f"{special_numeric}\n")   # write counts of special numeric 

# Close the file
file.close()
