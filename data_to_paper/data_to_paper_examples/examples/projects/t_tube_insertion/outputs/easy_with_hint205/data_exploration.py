
import pandas as pd

# loading the dataset
df = pd.read_csv('tracheal_tube_insertion.csv')

# opening a file to write the summary
with open('data_exploration.txt', 'w') as file:

    # Data Size
    file.write("# Data Size\n")
    file.write(f"Number of rows: {df.shape[0]}\n")
    file.write(f"Number of columns: {df.shape[1]}\n\n")

    # Summary Statistics
    file.write("# Summary Statistics\n")
    file.write(df.describe().to_string())
    file.write("\n\n")

    # Categorical Variables
    file.write("# Categorical Variables\n")
    # Checking if sex is the only categorical variable
    categorical_cols = df.select_dtypes(include='object').columns.tolist()
    if 'sex' in categorical_cols:
        file.write('Sex Variable Most common values:\n')
        file.write(df['sex'].value_counts().to_string())
    else: 
        file.write('There are no categorical variables in the dataset.\n')
    file.write("\n\n")
    
    # Missing Values
    file.write("# Missing Values\n")
    file.write(df.isnull().sum().to_string())
    file.write('\n')
    
    # Check for unknown/undefined numeric values if mentioned in "Description of the Dataset"
    # But this information was not provided, so I'm skipping this part.
    
file.close()
