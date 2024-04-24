
import pandas as pd

# Load data
df = pd.read_csv("tracheal_tube_insertion.csv")

# Open output file
with open('data_exploration.txt', 'w') as f:
    # Data Size
    f.write('# Data Size\n')
    f.write('Number of rows: {}\n'.format(df.shape[0]))
    f.write('Number of columns: {}\n\n'.format(df.shape[1]))
    
    # Summary Statistics
    f.write('# Summary Statistics\n')
    summary = df.describe(include='all') # summary statistics for all variables
    f.write('{}\n\n'.format(summary))
    
    # Categorical Variables
    f.write('# Categorical Variables\n')
    # In this case "sex" is the only categorical variable
    most_common = df['sex'].mode()[0] # Get the most common value
    f.write('Most common value for sex: {}\n\n'.format(most_common))

    # Missing Values
    f.write('# Missing Values\n')
    missing_values = df.isnull().sum() # Counts of missing values for each column
    f.write('{}\n\n'.format(missing_values))
    nan_values = (df == 'Nan').sum() # Counts of 'Nan' values for each column
    f.write('Counts of "Nan" values: {}\n\n'.format(nan_values))
    
f.close()
