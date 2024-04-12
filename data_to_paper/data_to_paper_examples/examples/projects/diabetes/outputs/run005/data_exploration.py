
# Import needed packages
import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Creating a text file
with open('data_exploration.txt', 'w') as f:
    # Data Size
    f.write("# Data Size\n")
    f.write("Number of rows: "+str(df.shape[0])+"\n")
    f.write("Number of columns: "+str(df.shape[1])+"\n\n")
    
    # Summary Statistics
    f.write("# Summary Statistics\n")
    f.write(str(df.describe())+"\n\n")
    
    # Categorical Variables
    categorical_vars = ['Diabetes_binary', 'HighBP', 'HighChol', 'CholCheck', 'Smoker', 'Stroke', 
                        'HeartDiseaseorAttack', 'PhysActivity', 'Fruits', 'Veggies', 'HvyAlcoholConsump',
                        'AnyHealthcare', 'NoDocbcCost', 'DiffWalk', 'Sex']
    f.write("# Categorical Variables\n")
    for var in categorical_vars:
        f.write("Most common value in "+var+": "+str(df[var].mode().values[0])+"\n")
    f.write("\n")

    # Missing Values
    f.write("# Missing Values\n")
    f.write("There are no missing values in the dataset as per the dataset description.")
    f.write("However, we still check:\n")
    df_missing = df.isnull().sum()
    # Check if there are any missing values at all
    if df_missing.sum() == 0:
        f.write("Confirmed, No missing values\n")
    else:
        f.write(str(df_missing[df_missing > 0]))
    f.write("\n\n")
    
    # Other summaries (if you find relevant given the dataset and your task)

# Close the file
f.close()
