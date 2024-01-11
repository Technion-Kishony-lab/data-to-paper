
# Import necessary packages
import pandas as pd
import numpy as np

# Load data
data = pd.read_csv("tracheal_tube_insertion.csv")

# Create a file for output
file = open('data_exploration.txt', 'w')

# Data Size
file.write('# Data Size\n')
file.write('Number of Patients : '+str(len(data))+'\n')
file.write('Number of Columns : '+str(len(data.columns))+'\n')
file.write('\n')

# Summary Statistics
file.write('# Summary Statistics\n')
desc = data.describe(include='all')
file.write(str(desc))
file.write('\n\n')

#Categorical Variables
file.write('# Categorical Variables\n')
file.write('Sex Distribution : \n'+str(data['sex'].value_counts())+'\n')
file.write('\n')

# Missing Values
file.write('# Missing Values\n')
missing_values = data.isnull().sum()
file.write('Missing values per column: \n'+str(missing_values)+'\n')

#Close file
file.close()
