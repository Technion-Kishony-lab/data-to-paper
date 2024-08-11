
# Required Libraries
import pandas as pd

# Loading the data
try:
    time_to_infection = pd.read_csv('TimeToInfection.csv')
    symptoms = pd.read_csv('Symptoms.csv')
except FileNotFoundError:
    raise FileNotFoundError("Input files TimeToInfection.csv or Symptoms.csv not found.")

# Creating the text file
try:
    with open("data_exploration.txt", "w") as file:
    
        # Data Size
        file.write("# Data Size\n")
        file.write("TimeToInfection.csv dimensions: " + str(time_to_infection.shape) + "\n")
        file.write("Symptoms.csv dimensions: " + str(symptoms.shape) + "\n")
    
        # Summary Statistics
        file.write("\n# Summary Statistics\n")
        file.write("TimeToInfection.csv summary: \n" + str(time_to_infection.describe()) + "\n")
        file.write("Symptoms.csv summary: \n" + str(symptoms.describe()) + "\n")
    
        # Categorical Variables
        file.write("\n# Categorical Variables\n")
        categorical_variables_tti = time_to_infection.dtypes[time_to_infection.dtypes == 'object'].index.tolist()
        categorical_variables_sbl = symptoms.dtypes[symptoms.dtypes == 'object'].index.tolist()
        for cat_var in categorical_variables_tti:
            file.write("TimeToInfection.csv - " + cat_var + ":\n" 
                        + str(time_to_infection[cat_var].value_counts()) + "\n")
        for cat_var in categorical_variables_sbl:
            file.write("Symptoms.csv - " + cat_var + ":\n" 
                        + str(symptoms[cat_var].value_counts()) + "\n")
    
        # Missing Values
        file.write("\n# Missing Values\n")
        file.write("TimeToInfection.csv missing values: \n" + str(time_to_infection.isnull().sum()) + "\n")
        file.write("Symptoms.csv missing values: \n" + str(symptoms.isnull().sum()) + "\n")
        
except Exception as err:
    raise Exception(f"An error occurred while writing the data exploration file: {str(err)}")
