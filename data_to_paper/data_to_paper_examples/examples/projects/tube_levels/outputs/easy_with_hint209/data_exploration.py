
import pandas as pd

# Load dataset
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open a new text file
with open('data_exploration.txt', 'w') as f:

    # Data size
    f.write('# Data Size\n')
    f.write('Number of rows: ' + str(df.shape[0])+'\n')
    f.write('Number of columns: ' + str(df.shape[1])+'\n\n')

    # Summary statistics
    f.write('# Summary Statistics\n')
    f.write(df.describe().to_string()+'\n\n')

    # Categorical variables
    f.write('# Categorical Variables\n')
    df_categorical = df.select_dtypes(include=['object'])
    for col in df_categorical.columns:
        f.write(str(col) + ' most common values: \n' + 
                df_categorical[col].value_counts().head(5).to_string() + '\n\n')

    # Missing values
    f.write('# Missing Values\n')
    f.write(df.isnull().sum().to_string()+'\n\n')

    # Check for special numeric values that stand for unknown/undefined
    f.write('# Special Numeric Values that Stand for Unknown/Undefined\n')
    special_values = ['?', '-', 'N/A', 'NA', 'na', 'nan', 'NaN', 'Nan', '--', 'unknown',
                      'Unknown', 'undefined', 'Undefined', 'null', 'None', 'none', 'Null']
    for special in special_values:
        if df.isin([special]).sum().sum() > 0:
            f.write(df.isin([special]).sum().to_string()+'\n\n')

f.close()
