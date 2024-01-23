
import pandas as pd

# Load data
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open the output file
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write("# Data Size\n")
    f.write("Num Rows: " + str(df.shape[0]) + "\n")
    f.write("Num Columns: " + str(df.shape[1]) + "\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    summary = df.describe()
    f.write(str(summary) + "\n\n")

    # Categorical Variables
    f.write("# Categorical Variables\n")
    if 'sex' in df.columns:
        f.write("Sex Counts:\n")
        f.write(str(df['sex'].value_counts()) + "\n\n")
    # continue with other categorical variables as needed...

    # Missing Values
    f.write("# Missing Values\n")
    missing = df.isnull().sum()
    f.write(str(missing) + "\n\n")
    
    # Numeric values that stand for unknown/undefined if any
    f.write("# Special numeric values that stand for unknown/undefined if any\n")
    f.write("Look at the 'Description of the Dataset' for any special undefined values and check their count here... \n\n")

    # Other summary as needed...
    f.write("# Other summary you deem relevant if any\n")
    f.write("Write here any additional summaries as needed... \n\n")
