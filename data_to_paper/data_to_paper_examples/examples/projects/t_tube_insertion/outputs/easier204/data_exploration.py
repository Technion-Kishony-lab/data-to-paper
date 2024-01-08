
# import required libraries
import pandas as pd
import numpy as np

# read the data
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open 'data_exploration.txt' in write mode 
with open('data_exploration.txt', 'w') as f:
    
    # Data Size
    f.write("# Data Size\n")
    f.write(f"Number of rows: {df.shape[0]}\n")
    f.write(f"Number of columns: {df.shape[1]}\n")

    # Summary statistics
    f.write("\n# Summary Statistics\n")
    summary_stats = df.describe()
    f.write(summary_stats.to_string())
    
    # Categorical Variables
    f.write("\n# Categorical Variables\n")
    f.write("Patient Sex (Most Common Value): " + str(df['sex'].mode()[0]) + "\n")

    # Missing Values
    f.write("\n# Missing Values\n")
    f.write(df.isnull().sum().to_string())
    
    # Check for any special numeric values
    f.write("\n# Special Numeric Values\n")
    special_values = df[df.columns].apply(lambda x: x.isin([-999, 999]).sum())
    f.write(special_values.to_string())
