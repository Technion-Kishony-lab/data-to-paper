

import pandas as pd

# Load the dataset
data = pd.read_csv("tracheal_tube_insertion.csv")

# Define functions which will generate various parts of the summary text
def data_size(df):
    return "# Data Size\n" + f"Number of Rows: {df.shape[0]} \nNumber of Columns: {df.shape[1]}\n"

def summary_stats(df):
    desc = df.describe(include='all').transpose()
    desc.index.name = 'Column'
    return "# Summary Statistics\n" + desc.to_string() + "\n"

def categorical_vars(df):
    cat_vars = df.select_dtypes(include=['object', 'bool', 'category'])
    if cat_vars.empty:
        return "# Categorical Variables\nNot Applicable\n"
    else:
        text = "# Categorical Variables\n"
        for col in cat_vars:
            text += df[col].value_counts().head().to_frame().rename({col: 'value_counts'}, axis=1).to_string(header=False)
            text += '\n'
        return text

def missing_values(df):
    num_missing = df.isnull().sum()
    nonzero_missing = num_missing[num_missing != 0].rename('num_missing')
    if nonzero_missing.empty:
        return "# Missing Values\nNot Applicable\n"
    else:
        return "# Missing Values\n" + nonzero_missing.to_string() + "\n"

# Other custom summary functions can be added here...

# Now put it all together
with open('data_exploration.txt', 'w') as f:
    f.write(data_size(data))
    f.write(summary_stats(data))
    f.write(categorical_vars(data))
    f.write(missing_values(data))
    # If any other summaries were defined, their functions could be called here
