
# required libraries
import pandas as pd

# load the csv file
df = pd.read_csv('tracheal_tube_insertion.csv')

# create output txt file
with open("data_exploration.txt", "w") as text_file:
    
    # Data Size
    text_file.write('# Data Size\n')
    text_file.write(f'Number of Rows: {df.shape[0]}\n')
    text_file.write(f'Number of Columns: {df.shape[1]}\n\n')

    # Summary Statistics
    text_file.write('# Summary Statistics\n')
    descriptive_stats = df.describe()
    text_file.write(descriptive_stats.to_string())
    text_file.write('\n\n')

    # Categorical Variables
    text_file.write('# Categorical Variables\n')
    text_file.write('Sex Distribution:\n')
    sex_distribution = df['sex'].value_counts()
    text_file.write(sex_distribution.to_string())
    text_file.write('\n\n')

    # Missing Values
    text_file.write('# Missing Values\n')
    missing_values = df.isnull().sum()
    text_file.write(missing_values.to_string())
    text_file.write('\n')

    # Checking for special numeric values standing for unknown/undefined.
    # According to provided dataset description there seems to be no such values. 
    # However, we check for any zero values that might be unusual in certain columns.
    text_file.write('Counts of zero in numerical variables where it might be unusual:\n')
    zero_counts = (df[['age_c', 'ht', 'wt', 'tube_depth_G']] == 0).sum()
    text_file.write(zero_counts.to_string())
    text_file.write('\n') 
