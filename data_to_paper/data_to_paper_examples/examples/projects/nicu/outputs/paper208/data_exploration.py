
import pandas as pd
import numpy as np

# load the data
df = pd.read_csv('meconium_nicu_dataset_preprocessed_short.csv')

# open a file to write the output 
with open('data_exploration.txt', 'w') as f:
    f.write("# Data Size\n")
    num_rows, num_cols = df.shape
    f.write(f'Number of Rows: {num_rows}\nNumber of Columns: {num_cols}\n\n')

    f.write("# Summary Statistics\n")
    summary_stats = df.describe(include='all').transpose() 
    summary_stats.to_string(f) 
    f.write('\n\n')

    f.write("# Categorical Variables\n")
    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        unique_values = df[col].unique()
        f.write(f'{col}: Unique values are {unique_values}\n')
    f.write('\n')

    f.write("# Missing Values\n")
    missing_counts = df.isnull().sum()
    for col in missing_counts.index:
        if missing_counts[col] > 0:
            f.write(f'{col}: {missing_counts[col]} missing values\n')
    f.write('\n')

    f.write("# Zero Values\n")
    num_cols = df.select_dtypes(include=['int64', 'float64']).columns
    for col in num_cols:
        zero_count = (df[col] == 0).sum()
        if zero_count > 0:
            f.write(f'{col}: {zero_count} zero values\n')

    f.write("\n# Specific Averages\n")
    avg_cols = ['AGE', 'GRAVIDA', 'PARA', 'HypertensiveDisorders', 'MaternalDiabetes',
                'FetalDistress', 'ProlongedRupture', 'Chorioamnionitis', 'GestationalAge', 'BirthWeight', 'APGAR1', 'APGAR5',
                'PPV', 'EndotrachealSuction', 'MeconiumRecovered', 'CardiopulmonaryResuscitation', 
                'RespiratoryReasonAdmission', 'RespiratoryDistressSyndrome', 'TransientTachypnea',
                'MeconiumAspirationSyndrome', 'OxygenTherapy', 'MechanicalVentilation',
                'Surfactant', 'Pneumothorax', 'AntibioticsDuration', 'Breastfeeding',
                'LengthStay', 'SNAPPE_II_SCORE']
    for col in avg_cols:
        avg = df[col].dropna().mean()  # calculating average after dropping NAN values
        f.write(f"{col} average: {avg}\n") 
    f.close()
