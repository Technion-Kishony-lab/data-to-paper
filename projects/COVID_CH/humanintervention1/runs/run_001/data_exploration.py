

import pandas as pd

# Load the data files into pandas DataFrames
time_to_infection = pd.read_csv("TimeToInfection.csv")
symptoms = pd.read_csv("Symptoms.csv")

# Create or open the output file
output_file = open("data_exploration.txt", 'w')

# Data Size
output_file.write("# Data Size\n")
output_file.write(f"TimeToInfection.csv - Rows: {time_to_infection.shape[0]}, Columns: {time_to_infection.shape[1]}\n")
output_file.write(f"Symptoms.csv - Rows: {symptoms.shape[0]}, Columns: {symptoms.shape[1]}\n\n")

# Summary Statistics
output_file.write("# Summary Statistics\n")
output_file.write("## TimeToInfection.csv\n")
output_file.write(time_to_infection.describe().to_string())
output_file.write("\n\n")
output_file.write("## Symptoms.csv\n")
output_file.write(symptoms.describe().to_string())
output_file.write("\n\n")

# Categorical Variables
output_file.write("# Categorical Variables\n")
output_file.write("## TimeToInfection.csv\n")
for col in time_to_infection.select_dtypes(include='object'):
    output_file.write(f"{col}:\n{time_to_infection[col].value_counts().head().to_string()}\n") 
output_file.write("\n")

output_file.write("## Symptoms.csv\n")
for col in symptoms.select_dtypes(include='object'):
    output_file.write(f"{col}:\n{symptoms[col].value_counts().head().to_string()}\n")
output_file.write("\n")

# Calculate and add interval lengths to "time_to_infection" DataFrame
time_to_infection['interval_length'] = time_to_infection['day_interval_stop'] - time_to_infection['day_interval_start']

# Write summary of interval lengths
output_file.write("# Interval Lengths for TimeToInfection.csv\n")
output_file.write(time_to_infection['interval_length'].describe().to_string())
output_file.write("\n\n")

# Missing Values
output_file.write("# Missing Values\n")
output_file.write("## TimeToInfection.csv\n")
output_file.write(time_to_infection.replace('', np.nan).isna().sum().to_string())
output_file.write("\n\n")
output_file.write("## Symptoms.csv\n")
output_file.write(symptoms.isna().sum().to_string())
output_file.write("\n\n")

number_of_unvaccinated_people = time_to_infection[(time_to_infection['group'] == 'N') | (time_to_infection['group'] == 'I')].shape[0]
output_file.write("# Number of unvaccinated people\n")
output_file.write(f"{number_of_unvaccinated_people}\n")

output_file.close()
