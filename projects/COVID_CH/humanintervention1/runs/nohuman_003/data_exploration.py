
import pandas as pd

data1 = pd.read_csv('TimeToInfection.csv')
data2 = pd.read_csv('Symptoms.csv')

with open("data_exploration.txt", "w") as file:
    # Data Size
    file.write("# Data Size\n")
    
    file.write(f"Number of rows in 'TimeToInfection.csv': {data1.shape[0]}\n")
    file.write(f"Number of columns in 'TimeToInfection.csv': {data1.shape[1]}\n")

    file.write(f"Number of rows in 'Symptoms.csv': {data2.shape[0]}\n")
    file.write(f"Number of columns in 'Symptoms.csv': {data2.shape[1]}\n")


    # Summary Statistics
    file.write("\n# Summary Statistics\n")
    
    file.write("\nSummary Statistics for 'TimeToInfection.csv':\n")
    file.write(str(data1.describe(include='all')) + "\n")

    file.write("\nSummary Statistics for 'Symptoms.csv':\n")
    file.write(str(data2.describe(include='all')) + "\n")


    # Categorical Variables
    file.write("\n# Categorical Variables\n")
    
    file.write("\nCategorical Variables for 'TimeToInfection.csv':\n")
    file.write(str(data1.select_dtypes(include=['object']).mode().transpose()) + "\n")

    file.write("\nCategorical Variables for 'Symptoms.csv':\n")
    file.write(str(data2.select_dtypes(include=['object']).mode().transpose()) + "\n")


    # Missing Values
    file.write("\n# Missing Values\n")
    
    file.write("\nMissing Values for 'TimeToInfection.csv':\n")
    file.write(str(data1.isnull().sum()) + "\n")

    file.write("\nMissing Values for 'Symptoms.csv':\n")
    file.write(str(data2.isnull().sum()) + "\n")
