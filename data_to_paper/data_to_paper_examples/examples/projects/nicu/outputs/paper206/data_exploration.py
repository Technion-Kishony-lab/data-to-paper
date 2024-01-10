
import pandas as pd

# Load the dataset
df = pd.read_csv('meconium_nicu_dataset_preprocessed_short.csv')

# List to store categorical variables
categorical_variables = []

# Writing data exploration results to the text file
with open('data_exploration.txt', 'w') as f:
    
    # Data Size
    f.write('# Data Size\n')
    f.write('Number of Rows: {}\n'.format(df.shape[0]))
    f.write('Number of Columns: {}\n'.format(df.shape[1]))

    # Summary Statistics
    f.write('\n# Summary Statistics\n')
    for col in df.columns:
        if df[col].dtype == 'object':
            categorical_variables.append(col)
            common_category = df[col].mode()[0]
            frequency = df[col].value_counts().max()
            f.write('\nSummary of Variable: {}\n'.format(col))
            f.write('Most Common Category: {} with Frequency of: {}\n'.format(common_category, frequency))
        else:
            mean = df[col].mean(skipna=True)  # Include 'skipna=True' to exclude NaN values in calculation
            if pd.notna(mean):  # Check if mean is not NaN before writing to file
                f.write('\nSummary of Variable: {}\n'.format(col))
                f.write('Mean: {}\n'.format(round(mean, 2)))  # Round to 2 decimal places
    
    # Categorical Variables
    f.write('\n# Categorical Variables\n')
    for v in categorical_variables:
        f.write('Categorical Variable: {}\n'.format(v))
      
    # Missing Values
    f.write('\n# Missing Values\n')
    missing_values = df.isna().sum()
    for col in missing_values.index:
        f.write('Missing Values in {}: {}\n'.format(col, missing_values[col]))
