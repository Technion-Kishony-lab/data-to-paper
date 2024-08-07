
# Import Required Libraries
import pandas as pd
import numpy as np

# Load Both Datasets
time_to_infection = pd.read_csv('TimeToInfection.csv')
symptoms = pd.read_csv('Symptoms.csv')

# Function to handle cases where mode cannot be determined
def safe_mode(series):
    try:
        return series.mode()[0]
    except KeyError:
        return np.nan

# Open Output File
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write('# Data Size\n')
    f.write(f'TimeToInfection.csv: {time_to_infection.shape[0]} rows, {time_to_infection.shape[1]} columns\n')
    f.write(f'Symptoms.csv: {symptoms.shape[0]} rows, {symptoms.shape[1]} columns\n\n')

    # Summary Statistics
    f.write('# Summary Statistics\n')
    f.write('TimeToInfection.csv:\n')
    f.write(time_to_infection.describe().to_string())
    f.write('\n\nSymptoms.csv:\n')
    f.write(symptoms.describe().to_string())
    f.write('\n\n')
    
    # Mean length of interval
    f.write('# Mean Length of Interval\n')
    mean_length_of_interval = (time_to_infection['day_interval_stop'] - time_to_infection['day_interval_start']).mean()
    f.write(f'The mean length of interval in TimeToInfection.csv: {mean_length_of_interval}\n\n')
    
    # Mean number of intervals per ID
    f.write('# Mean Number of Intervals per ID\n')
    mean_intervals_per_id = time_to_infection['ID'].value_counts().mean()
    f.write(f'The mean number of intervals per ID in TimeToInfection.csv: {mean_intervals_per_id}\n\n')

    # Categorical Variables
    f.write('# Categorical Variables\n')
    # Compute categorical values per unique ID
    f.write('TimeToInfection.csv:\n')
    for col in ["group", "vaccinetype"]:
        f.write(f'Values per ID for {col}: \n')
        f.write(time_to_infection.groupby('ID')[col].apply(safe_mode).replace('', 'not vaccinated').value_counts().to_string())
        f.write('\n')

    f.write('\nSymptoms.csv:\n')
    for col in ["group"]:
        f.write(f'Values for {col}:\n')
        f.write(symptoms[col].value_counts().to_string())
        f.write('\n')

    # Missing Values
    f.write('\n# Missing Values\n')
    # Compute missing values per unique ID
    f.write('TimeToInfection.csv:\n')
    f.write(time_to_infection.groupby('ID').apply(lambda x: x.isnull().sum()).sum().to_string())
    f.write('\n\nSymptoms.csv:\n')
    f.write(symptoms.isnull().sum().to_string())
    f.write('\n')

f.close()
