
import pandas as pd

# Load in the csv file
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open a file to write the exploration data to 
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write('# Data Size\n')
    f.write('Number of rows: ' + str(df.shape[0]) + '\n')
    f.write('Number of columns: ' + str(df.shape[1]) + '\n\n')

    # Summary Statistics
    f.write('# Summary Statistics\n')
    f.write(str(df.describe()) + '\n\n')

    # Categorical Variables
    f.write('# Categorical Variables (if any)\n')
    for cols in df.columns:
        if df[cols].dtype == 'object':
            f.write(f"{cols}'s distribution:\n")
            f.write(str(df[cols].value_counts().head()) + '\n\n')

    # Missing Values
    f.write('# Missing Values\n')
    f.write(str(df.isnull().sum()) + '\n\n')

    # Checking for special values
    # Special values are checked after missing value analysis to 
    # avoid double counting of missing and special values
    f.write('# Special Numeric Values\n')
    special_count = (df==9999).sum()  # Note, replace "9999" with the special numeric value informed in your data description if any.
    f.write(str(special_count[special_count > 0]) + '\n\n')  
          
    # Add any customizable summary of your preference here
