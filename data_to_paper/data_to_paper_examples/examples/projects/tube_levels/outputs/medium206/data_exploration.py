
import pandas as pd

# Load data
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open a file for output
with open("data_exploration.txt", "w") as out_file:
    
    # Data size
    out_file.write("# Data Size\n")
    out_file.write("Number of rows: " + str(df.shape[0]) + "\n")
    out_file.write("Number of columns: " + str(df.shape[1]) + "\n\n")
    
    # Summary Statistics
    out_file.write("# Summary Statistics\n")
    out_file.write(df.describe().to_string())  # Full summary of every column
    out_file.write("\n\n")
    
    # Categorical Variables
    out_file.write("# Categorical Variables\n")
    categorical_variables = df.select_dtypes(include=['object']).columns
    for variable in categorical_variables:
        out_file.write("\nVariable: " + variable + "\n")
        out_file.write("Most common values:\n")
        out_file.write(df[variable].value_counts().head().to_string())
        
    out_file.write("\n\n")
    
    # Missing Values
    out_file.write("# Missing Values\n")
    out_file.write(df.isnull().sum().to_string())  # Count of missing values

    out_file.write("\n\n")
    
    # Other measures of interest:
    # for example, let's count the number of unique values per column
    out_file.write("# Unique values per column\n")
    out_file.write(df.nunique().to_string())
    
    out_file.write("\n\n")
