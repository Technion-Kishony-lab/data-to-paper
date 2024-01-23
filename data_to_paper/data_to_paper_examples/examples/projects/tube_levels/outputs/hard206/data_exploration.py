
import pandas as pd

# Load the data from the csv file
df = pd.read_csv('tracheal_tube_insertion.csv')

# Open our output text file
with open("data_exploration.txt", "w") as file:

    # Print the size of the data
    file.write('# Data Size\n')
    file.write(f'Number of rows: {df.shape[0]}\n')
    file.write(f'Number of columns: {df.shape[1]}\n\n')

    # Print the summary statistics for key numeric variables
    file.write('# Summary Statistics\n')
    file.write(df[['tube', 'age_c', 'ht', 'wt', 'tube_depth_G']].describe().to_string())
    file.write('\n\n')

    # Print some details about categorical variables
    file.write('# Categorical Variables\n')
    file.write('Variable "sex" - 0: Female, 1: Male\n')
    file.write(df['sex'].value_counts().to_string())
    file.write('\n\n')

    # Identify and print missing values count
    file.write('# Missing Values\n')
    for col in df.columns:
        missing_count = df[col].isnull().sum()
        if missing_count > 0:
            file.write(f'{col} missing count: {missing_count}\n')
    file.write('\n\n')

    # Or if no Missing Values
    file.write('No missing values detected\n')


# Close file
file.close()
