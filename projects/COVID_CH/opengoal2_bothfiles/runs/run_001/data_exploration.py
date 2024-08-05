
# Importing required Libraries
import pandas as pd
import numpy as np

# Loading the csv files
TimeToInfection_df = pd.read_csv('TimeToInfection.csv')
Symptoms_df = pd.read_csv('Symptoms.csv')

# Writing outputs to a text file
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write("# Data Size\n")
    f.write(f"TimeToInfection data: {TimeToInfection_df.shape[0]} rows, {TimeToInfection_df.shape[1]} columns\n")
    f.write(f"Symptoms data: {Symptoms_df.shape[0]} rows, {Symptoms_df.shape[1]} columns\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    f.write("TimeToInfection data:\n")
    f.write(TimeToInfection_df.describe().to_string())
    f.write("\n\nSymptoms data:\n")
    f.write(Symptoms_df.describe().to_string())
    f.write("\n\n")

    # Categorical Variables
    f.write("# Categorical Variables\n")
    categorical_columns_TimeToInfection = TimeToInfection_df.select_dtypes(['object']).columns
    for col in categorical_columns_TimeToInfection:
        f.write(f"TimeToInfection data - {col} : Most common value - {TimeToInfection_df[col].mode()[0]}\n")
    categorical_columns_Symptoms = Symptoms_df.select_dtypes(['object']).columns
    for col in categorical_columns_Symptoms:
        f.write(f"Symptoms data - {col} : Most common value - {Symptoms_df[col].mode()[0]}\n")

    # Missing Values
    f.write("\n# Missing Values\n")
    f.write("TimeToInfection data Missing values:\n")
    f.write(TimeToInfection_df.isnull().sum().to_string())
    f.write("\n\nSymptoms data Missing values:\n")
    f.write(Symptoms_df.isnull().sum().to_string())
    f.write("\n")

