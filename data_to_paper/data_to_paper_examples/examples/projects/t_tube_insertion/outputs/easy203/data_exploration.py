
# necessary libraries
import pandas as pd

# loading the CSV dataset
dataset = pd.read_csv('tracheal_tube_insertion.csv')

# Creating the output text file
with open('data_exploration.txt', 'w') as file:
    
    # Data Size
    file.write('# Data Size\n')
    file.write('Number of Rows: ' + str(dataset.shape[0]) + '\n')
    file.write('Number of Columns: ' + str(dataset.shape[1]) + '\n\n')
    
    # Summary Statistics
    file.write('# Summary Statistics\n')
    file.write(str(dataset.describe()) + '\n\n')
    
    # Categorical Variables
    file.write('# Categorical Variables\n')
    # Assuming 'sex' is the only categorical variable
    sex_groupby = dataset.groupby("sex").size().reset_index(name='Counts')
    file.write(str(sex_groupby) + '\n\n')
    
    # Missing Values
    file.write('# Missing Values\n')
    file.write(str(dataset.isnull().sum()) + '\n\n')

file.close()
