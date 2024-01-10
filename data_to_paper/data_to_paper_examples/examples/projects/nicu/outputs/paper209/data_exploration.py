
import pandas as pd
import numpy as np

# Load the data
data = pd.read_csv('meconium_nicu_dataset_preprocessed_short.csv')

# Determine categorical and numerical columns
cat_columns = ['PrePost', 'HypertensiveDisorders', 'MaternalDiabetes', 'ModeDelivery', 'FetalDistress', 'ProlongedRupture', 'Chorioamnionitis', 'Sepsis', 'Gender', 'PPV', 'EndotrachealSuction', 'MeconiumRecovered', 'CardiopulmonaryResuscitation', 'ReasonAdmission', 'RespiratoryReasonAdmission', 'RespiratoryDistressSyndrome', 'TransientTachypnea', 'MeconiumAspirationSyndrome', 'OxygenTherapy', 'MechanicalVentilation', 'Surfactant', 'Pneumothorax', 'Breastfeeding']
num_columns = ['AGE', 'GRAVIDA', 'PARA', 'GestationalAge', 'BirthWeight', 'APGAR1', 'APGAR5', 'AntibioticsDuration', 'LengthStay', 'SNAPPE_II_SCORE']

# Open output file
with open('data_exploration.txt', 'w') as f:

    # Writing Data Size
    f.write('# Data Size\n')
    f.write('Number of Rows: {}\n'.format(data.shape[0]))
    f.write('Number of Columns: {}\n\n'.format(data.shape[1]))

    # Writing Summary Statistics for numerical variables
    f.write('# Summary Statistics\n')
    summary_stats = data[num_columns].describe()
    f.write('Numerical variables:\n{}\n\n'.format(summary_stats))

    # Writing Information on Categorical Variables
    f.write('# Categorical Variables\n')
    for var in cat_columns:
        f.write('Variable "{}": {} unique values, most common: {}\n'.format(var, data[var].nunique(), data[var].mode().values[0]))
    f.write('\n')

    # Writing Information on Missing Values
    f.write('# Missing Values\n')
    missing_values = data.isnull().sum()
    missing_values_flag = False
    for col, n_missing in missing_values.items():
        if n_missing > 0:
            missing_values_flag = True
            f.write('Column "{}": {} missing values\n'.format(col, n_missing))
    if not missing_values_flag:
        f.write('No missing data found\n\n')

    # Handle missing values after writing the counts into the file, by replacing them with the mode
    # for categorical features and mean for numerical features
    for col in cat_columns:
        data[col].fillna(data[col].mode()[0], inplace=True)
    for col in num_columns:
        data[col].fillna(data[col].mean(), inplace=True)

    # Writing Information on Special Numeric Values
    f.write('# Special Numeric Values\n')
    special_values_detected = False
    for col in num_columns:
        n_special = sum(data[col] == -999) + sum(data[col] == -1) + sum(data[col] == -9999) + sum(data[col] == 9999)
        if n_special > 0:
            special_values_detected = True
            f.write('Column "{}": {} rows with special numeric values (-999, -1, 9999, -9999)\n'.format(col, n_special))
    if not special_values_detected:
        f.write('No special numeric values detected\n')
    f.write('\n')

    # Additional Summary If Needed
    f.write('# Additional Summary\n')
    n_pre = sum(data['PrePost'] == 0)
    n_post = sum(data['PrePost'] == 1)
    f.write('PrePost: Pre-2015: {} rows, Post-2015: {} rows\n'.format(n_pre, n_post))
