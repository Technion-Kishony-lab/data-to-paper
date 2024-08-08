
# Import required libraries
import pandas as pd
import numpy as np

# Load the datasets
TimeToInfection = pd.read_csv('TimeToInfection.csv')
Symptoms = pd.read_csv('Symptoms.csv')

# OPEN the output file to write the exploration summary
file = open('data_exploration.txt','a')

########################################
# -- Data Size
# Write the number of rows and columns of the datasets to the output file
file.write('# Data Size\n\n')

size_TTI = TimeToInfection.shape 
size_S = Symptoms.shape 

file.write(f'TimeToInfection.csv: {size_TTI[0]} rows, {size_TTI[1]} columns\n')
file.write(f'Symptoms.csv: {size_S[0]} rows, {size_S[1]} columns\n\n')

########################################
# -- Summary Statistics
# Write summary statistics of continuous variables
file.write('# Summary Statistics\n\n')

summary_age_TTI = TimeToInfection['age'].describe()
summary_age_S = Symptoms['age'].describe()

file.write(f'TimeToInfection.csv variable "age":\n{summary_age_TTI}\n')
file.write(f'Symptoms.csv variable "age":\n{summary_age_S}\n\n')

########################################
# -- Categorical Variables
# Write the most common value of each categorical variable 
file.write('# Categorical Variables\n\n')

most_common_TTI = TimeToInfection.select_dtypes(['object']).mode().iloc[0]
most_common_S = Symptoms.select_dtypes(['object']).mode().iloc[0]

file.write(f'TimeToInfection.csv most common values:\n{most_common_TTI}\n')
file.write(f'Symptoms.csv most common values:\n{most_common_S}\n\n')

########################################
# -- Missing Values
# Write the count of missing values in the datasets 
file.write('# Missing Values\n\n')

missing_TTI = TimeToInfection.isna().sum()
missing_S = Symptoms.isna().sum()

file.write(f'TimeToInfection.csv missing values:\n{missing_TTI[missing_TTI > 0]}\n')
file.write(f'Symptoms.csv missing values:\n{missing_S[missing_S > 0]}\n\n')

###################################################
# -- Close the file
file.close()
