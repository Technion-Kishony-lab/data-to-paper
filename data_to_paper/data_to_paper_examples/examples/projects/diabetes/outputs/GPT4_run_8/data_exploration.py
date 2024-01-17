
import pandas as pd
import numpy as np

# read the csv file
data = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# create a text file
file = open("data_exploration.txt", "w")

# Measure the scale of the data
file.write("# Data Size\n")
file.write("Number of Rows:" + str(data.shape[0]) + "\n")
file.write("Number of Columns:" + str(data.shape[1]) + "\n\n")

# Summary statistics of all variables
file.write("# Summary Statistics\n")
summary = data.describe(include='all')
file.write(str(summary) + "\n\n")

# As applicable, list here categorical values and their most common values
file.write("# Categorical Variables\n")
for col in data.columns:
    if data[col].dtype == "object":
        file.write("Column: "+str(col)+"\n")
        file.write("Most Common Values:\n"+str(data[col].value_counts().idxmax())+"\n\n")
        
# Counts of missing, unknown, or undefined values
file.write("# Missing Values\n")
missing = data.isnull().sum()
file.write("Missing values per column:\n" + str(missing) + "\n")

# Counts of special numeric values that stand for unknown/undefined if any
file.write("# Special Numeric Values\n")
for col in data.columns:
    if data[col].dtype == "int64" or data[col].dtype == "float64":
        file.write("Column: "+str(col)+"\n")
        file.write("Count of Undefined/Unknown Values:\n" + str(((data[col]==-1) | (data[col]==99)).sum())+"\n")

# close the file
file.close()
