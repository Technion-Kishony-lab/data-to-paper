
import pandas as pd

# Function to compute and write summary of data to a file
def data_summary(df, missing_dict):

    # Data Size
    rows, columns = df.shape

    # Summary Statistics
    summary_stats = df.describe().to_string()

    # Categorical Variables
    cat_vars = [col for col in df.columns if df[col].nunique() < 10]  # Assuming a variable is categorical if it has less than 10 unique values
    freq_counts = [df[col].value_counts().idxmax() for col in cat_vars]
    categorical_values = pd.DataFrame(freq_counts, index=cat_vars, columns=['Most common value']).to_string()

    # Missing Values
    missing_values = df.isin(list(missing_dict.keys())).sum().to_string()

    # Writing to the Output File
    with open('data_exploration.txt', 'w') as f:
        f.write('# Data Size\n')
        f.write(f'Number of rows: {rows}\n')
        f.write(f'Number of columns: {columns}\n\n')

        f.write('# Summary Statistics\n')
        f.write(summary_stats + '\n\n')

        f.write('# Categorical Variables\n')
        f.write(categorical_values + '\n\n')

        f.write('# Missing Values\n')
        f.write(missing_values + '\n\n')

# Define a dictionary for missing value representations in the dataset
missing_dict = {99: 'unknown', 98: 'undefined'}

# Load the dataset
df = pd.read_csv("data.csv")

# Replace missing value representations in the dataset with NaN
for key, value in missing_dict.items():
    df.replace(key, pd.NA, inplace=True)

# Call the data_summary function
data_summary(df, missing_dict)
