
import pandas as pd

# Read the data file
data = pd.read_csv("tracheal_tube_insertion.csv")

# Open the output file to store the summaries
exploration_file = open('data_exploration.txt', 'w')

# Data size
exploration_file.write('# Data Size\n')
exploration_file.write('Number of Rows: {}\n'.format(data.shape[0]))
exploration_file.write('Number of Columns: {}\n'.format(data.shape[1]))

# Summary Statistics
exploration_file.write('\n# Summary Statistics\n')
exploration_file.write(data.describe().to_string())

# Categorical Variables
exploration_file.write('\n# Categorical Variables\n')
categorical_variables = data.select_dtypes(include=['object']).columns.tolist()
for variable in categorical_variables:
    top_values = data[variable].value_counts().nlargest(5).to_string()
    exploration_file.write('\n{}\n{}\n'.format(variable, top_values))

# Missing Values
exploration_file.write('\n# Missing Values\n')
missing_values = data.isnull().sum().to_string()
exploration_file.write(missing_values)

exploration_file.close()
