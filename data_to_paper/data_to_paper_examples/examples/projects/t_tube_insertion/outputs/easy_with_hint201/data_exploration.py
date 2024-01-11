
import pandas as pd
import numpy as np

# Load the Data
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open a file to write the output
with open('data_exploration.txt','w') as outfile:
   
    # Data Size
    outfile.write("# Data Size\n")
    outfile.write("Number of Rows: " + str(df.shape[0]) + "\n")
    outfile.write("Number of Columns: " + str(df.shape[1]) + "\n\n")

    # Summary Statistics
    outfile.write("# Summary Statistics\n")
    outfile.write(str(df.describe()) + "\n\n")

    # Categorical Variables
    outfile.write("# Categorical Variables\n")
    categorical_columns = df.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        outfile.write("Most Common Value for "+ col +": " + str(df[col].mode().values[0]) + "\n")
    outfile.write("\n")

    # Missing Values
    outfile.write("# Missing Values\n")
    outfile.write("Missing or undefined values for each column:\n" + str(df.isnull().sum()) + "\n\n")
    outfile.write("Special numeric values that stand for unknown/undefined if any:\n")
    for col in df.columns:
        if df[col].dtype in ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']:
            outfile.write("Column "+ col +" contains "+ str(df[df[col] < 0].shape[0]) +" negative values.\n")
            
# Close the file        
outfile.close()
