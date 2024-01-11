
# Importing the necessary modules
import pandas as pd

# Load the dataset
df = pd.read_csv('tracheal_tube_insertion.csv')

# Create a text file that will contain the data exploration summary
f = open("data_exploration.txt", "w")

# Data Size
f.write("# Data Size\n")
f.write("Number of rows: {}\n".format(df.shape[0]))
f.write("Number of columns: {}\n\n".format(df.shape[1]))

# Summary Statistics
f.write("# Summary Statistics\n")
summary = df.describe().transpose()
f.write('{}\n\n'.format(summary))

# Categorical Variables
f.write("# Categorical Variables\n")
for column in df.select_dtypes(include=['object']).columns:
    f.write("Variable: {}\n".format(column))
    f.write("Most common values:\n")
    f.write('{}\n\n'.format(df[column].mode()))

# Missing Values
f.write("# Missing Values\n")
missing_values = df.isnull().sum()
f.write('{}\n\n'.format(missing_values))

f.close()
