
import pandas as pd

# read the dataset
data = pd.read_csv('tracheal_tube_insertion.csv')

# Data size
data_size = data.shape

# Summary Statistics
summary_stats = data.describe(include='all')

# Categorical Variables
categorical_vars = data.select_dtypes(include=['object']).nunique()

# Most common categories
most_common_cats = data.select_dtypes(include=['object']).mode()

# Missing Values
missing_values = data.isnull().sum()

# Checking for special numeric values that stand for unknown/undefined
# In this dataset, there's no such numeric value which represents unknown/undefined

# Save the results to a text file
with open('data_exploration.txt', 'w') as file:
    file.write("# Data Size\n")
    file.write(f"Number of rows: {data_size[0]}\n")
    file.write(f"Number of columns: {data_size[1]}\n\n")
    
    file.write("# Summary Statistics\n")
    file.write(f"{summary_stats}\n\n")
    
    file.write("# Categorical Variables\n")
    if len(categorical_vars) == 0:
        file.write("There are no categorical variables in the dataset.")
    else:
        file.write(f"{categorical_vars}\n")
        file.write(f"Most common categories:\n {most_common_cats}\n")
        
    file.write("\n# Missing Values\n")
    file.write(f"{missing_values}\n\n")

    # add any additional exploratory data analysis here
    # for example, you could check for outlier values, or analyze patterns of missing data

    # end of the file
