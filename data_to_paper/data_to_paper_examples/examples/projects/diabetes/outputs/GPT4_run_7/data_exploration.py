
import pandas as pd

# Read the data
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Open a file for writing
with open("data_exploration.txt", "w") as text_file:

    # Data Size
    text_file.write("# Data Size\n")
    text_file.write("Number of rows: {}\n".format(df.shape[0]))
    text_file.write("Number of columns: {}\n".format(df.shape[1]))
    text_file.write("\n")

    # Summary Statistics
    text_file.write("# Summary Statistics\n")
    desc = df.describe(include='all')
    text_file.write("{}\n".format(desc))
    text_file.write("\n")

    # Categorical Variables
    text_file.write("# Categorical Variables\n")
    categorical_vars = df.select_dtypes(include=['object']).columns
    for var in categorical_vars:
        top = df[var].describe()['top']
        text_file.write("Most common value for {}: {}\n".format(var, top))
    text_file.write("\n")

    # Missing Values
    text_file.write("# Missing Values\n")
    missing_values = df.isnull().sum()
    text_file.write("{}\n".format(missing_values))
    text_file.write("\n")
