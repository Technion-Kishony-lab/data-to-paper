

import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open the output file in write mode
with open('data_exploration.txt', 'w') as f:

    # Data size
    f.write('# Data Size\n')
    f.write('Number of rows: ' + str(df.shape[0]) + '\n')
    f.write('Number of columns: ' + str(df.shape[1]) + '\n\n')

    # Summary statistics
    f.write('# Summary Statistics\n')
    # Generate summary statistics for numerical columns
    summary_stats = df.describe().transpose() 
    f.write(str(summary_stats))
    f.write('\n\n')
    
    #Categorical Variables
    f.write('# Categorical Variables\n')
    f.write("Sex (0=female, 1=male):\n")
    f.write(str(df['sex'].value_counts()))
    f.write('\n\n')
    
    # Missing values
    f.write('# Missing Values\n')
    missing_values = df.isna().sum() 
    f.write(str(missing_values))
    f.write('\n\n')
    
    # Check for special values that represent 'female' and 'newborn'
    f.write('# Special Numeric Values\n')
    special_values = (df==0).sum()
    special_values_str = special_values[special_values > 0].to_string()
    if special_values_str != "":
        f.write("Counts of special numeric values (0's) representing 'female' and 'newborn':\n")
        f.write(str(special_values_str))
        f.write('\n\n')

    # Outliers
    f.write('# Outliers\n')
    Q1 = df.quantile(0.25)
    Q3 = df.quantile(0.75)
    IQR = Q3 - Q1
    outlier_counts = ((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))).sum()
    outlier_counts_str = outlier_counts[outlier_counts > 0].to_string()
    if outlier_counts_str != "":
        f.write("Counts of values falling outside the interquartile range (IQR) - potential outliers:\n")
        f.write(str(outlier_counts_str))
        f.write('\n')
    else:
        f.write("No potential outliers identified using IQR method.\n")
        
