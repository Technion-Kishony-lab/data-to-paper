
import pandas as pd

# Load the dataset
df = pd.read_csv("tracheal_tube_insertion.csv")

# Open a file for writing
with open('data_exploration.txt', 'w') as file:

    # Data size
    file.write('# Data Size\n')
    file.write(f'Number of rows: {df.shape[0]}\n')
    file.write(f'Number of columns: {df.shape[1]}\n')
    file.write('\n')

    # Summary Statistics
    file.write('# Summary Statistics\n')
    file.write(df.describe().to_string())
    file.write('\n')

    # Categorical Variables
    file.write('\n# Categorical Variables\n')
    for col in df.select_dtypes(include=['object']).columns:
        file.write(f'{col} most common values:\n')
        file.write(df[col].value_counts().head(5).to_string())
        file.write('\n')

    # Missing Values
    file.write('\n# Missing Values\n')
    file.write(df.isnull().sum().to_string())
