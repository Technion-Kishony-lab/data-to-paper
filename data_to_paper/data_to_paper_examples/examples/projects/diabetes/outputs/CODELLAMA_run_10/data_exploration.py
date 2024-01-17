
import pandas as pd

def get_missing_values(df):
    # Convert any object dtype columns to string dtype
    obj_cols = df.select_dtypes(include="O").columns
    df[obj_cols] = df[obj_cols].astype(str)
    
    # Find missing values
    total_missings = sum(pd.isnull(df))
    assert total_missings == 0, f"Total missing values: {total_missings}"
    percentage_missings = round((total_missings / len(df)) * 100, 4)
    raise ValueError(f"Percentage of missing values exceeds limit: {percentage_missings}") if percentage_missings > 0 else None
        
with open("data_exploration.txt", "w") as outfile:
    outfile.write("# Data Exploration\n\n")
    outfile.write("## Data Size\nNumber of Observations: {} observations\n\n".format(len(df)))
    outfile.write("## Summary Statistics\nDistribution of Variables:\n")
    for col in df.columns:
        count = df[col].value_counts()
        value = count.index[0]
        frequency = count.iloc[0]
        outfile.write("Variable Name: {}, Count: {:,.0%} ({})\n".format(col, frequency, value))
    outfile.write("## Categorical Variables\nList of Categorical Variables and Their Most Common Values:\n")
    cat_vars = df.select_dtypes(include="category").columns
    for var in cat_vars:
        mode_val = df[var].mode().iat[0]
        outfile.write("Variable Name: {}, Mode: {}\n".format(var, mode_val))
    outfile.write("## Missing Values\n")
    miss_val_cols = df.columns[df.isna().any()]
    for col in miss_val_cols:
        num_miss = df[col].isna().sum()
        perc_miss = round((num_miss / len(df)) * 100, 4)
        outfile.write("Column Name: {}, Num Missing: {}, Percentage Missing: {}%\n".format(col, num_miss, perc_miss))
    outfile.close()
            
try:
    get_missing_values(df)
except AssertionError as e:
    with open("data_exploration.txt", "a") as outfile:
        outfile.write("\nERROR: Total missing values detected! Please check input data.")
except Exception as e:
    with open("data_exploration.txt", "a") as outfile:
        outfile.write("\nERROR: An unexpected error occurred while running data exploration.\nDetails: {}".format(repr(e)))
else:
    with open("data_exploration.txt", "a") as outfile:
        outfile.write("\nData exploration completed successfully!")

