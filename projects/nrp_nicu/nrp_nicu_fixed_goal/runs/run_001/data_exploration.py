
import pandas as pd
import numpy as np

# Loading the Dataset
df = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# Open text file
with open("data_exploration.txt", "w") as file:

    # Data Size
    file.write("# Data Size\n")
    file.write("Number of rows: "+ str(df.shape[0])+ "\n")
    file.write("Number of columns: "+ str(df.shape[1]) + "\n")
    
    # Summary Statistics
    file.write("\n# Summary Statistics\n")
    file.write(df.describe(include="all").transpose().to_string())

    # Categorical Variables
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    file.write("\n# Categorical Variables\n")
    for col in categorical_cols:
        top_freq = df[col].value_counts().idxmax()
        file.write(f'Column: {col} | Most common value: {top_freq}\n')

    # Missing Values
    file.write("\n# Missing Values\n")
    file.write(df.isnull().sum().to_string())

    # Checking if any special numeric values are used for unknown/undefined entries, as described in the "Description of the Dataset"
    # No such numeric values are described in the dataset description for this case, so this section is Not Applicable in this case
    file.write("\n# Special Numeric Values Representing Unknown/Undefined\n")
    file.write("# Not Applicable\n")

    file.close()
