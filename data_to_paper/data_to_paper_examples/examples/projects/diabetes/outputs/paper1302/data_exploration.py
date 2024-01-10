
import pandas as pd

# Load dataset
data = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Open output file
with open('data_exploration.txt', 'w') as f: 
    
    ## Data size
    f.write('# Data Size\n')
    f.write('Number of Rows: {}\n'.format(data.shape[0]))
    f.write('Number of Columns: {}\n\n'.format(data.shape[1]))

    ## Summary Statistics for key numerical variables
    keys = ['BMI', 'GenHlth', 'MentHlth', 'PhysHlth', 'Age', 'Education', 'Income']
    summary = data[keys].describe()

    f.write('# Summary Statistics\n')
    f.write('{}\n\n'.format(summary))

    ## Categorical Variables
    f.write('# Categorical Variables\n')
    categorical_columns = data.select_dtypes(include=['object','bool']).columns
    
    for column in categorical_columns:
        most_common = data[column].value_counts().idxmax()
        f.write('{}: Most common value is {}\n'.format(column, most_common))

    f.write('\n')

    ## Missing Values
    missing_values = data.isnull().sum()
    f.write('# Missing Values\n')
    f.write('{}\n\n'.format(missing_values))

    # Unknown/undefined values
    f.write('# Unknown/undefined values\n')
    for column in data.columns:
        count = data[data[column] == 99].shape[0]  # assuming 99 is the unknown/undefined value based on the dataset description
        f.write('{}: Number of unknown/undefined values: {}\n'.format(column, count))

f.close()
