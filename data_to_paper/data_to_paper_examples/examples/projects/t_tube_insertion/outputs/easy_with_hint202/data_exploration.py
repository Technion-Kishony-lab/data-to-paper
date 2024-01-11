
import pandas as pd
import numpy as np 

# load the dataset
df = pd.read_csv("tracheal_tube_insertion.csv")

header = ['Data Size', 'Summary Statistics', 'Categorical Variables', 'Missing Values']

# count of rows and columns
data_size = "Number of Rows: {}\nNumber of Columns: {}".format(df.shape[0], df.shape[1])

# summary statistics
summary_stats = df.describe(include='all').transpose().to_string()

# unique values in categorical variable
cat_vars = "sex: {}".format(df.sex.value_counts().to_string())

# check count of missing values in all columns
missing_values = df.isnull().sum().to_string()

exploratory_outputs = [data_size, summary_stats, cat_vars, missing_values]

with open("data_exploration.txt", 'w') as f:
    for i,section in enumerate(exploratory_outputs):
        f.write("# " + header[i] + "\n" + section + "\n\n")
