
import pandas as pd

# reading the dataset
df = pd.read_csv('tracheal_tube_insertion.csv')

with open('data_exploration.txt', 'w') as file:

    # writing data size
    file.write("# Data Size\n")
    data_size = df.shape
    file.write(f"Number of rows: {data_size[0]}\nNumber of columns: {data_size[1]}\n\n")

    # writing summary statistics
    file.write("# Summary Statistics\n")
    stats = df.describe(include='all')
    file.write(f"{stats}\n\n")

    # writing categorical variable stats
    file.write("# Categorical Variables\n")
    categorical_variables_freq = df.loc[:, df.dtypes == object].apply(lambda x: x.value_counts().index[0] if len(x.value_counts())>0 else 'no values present')
    file.write(f"{categorical_variables_freq}\n\n")

    # writing missing values
    file.write("# Missing Values\n")
    missing_counts = df.isnull().sum()
    file.write(f"{missing_counts}\n\n")
    
    # Check for special numeric values which stand for unknown/undefined. Here, we assume that negative values are used to stand for unknown/undefined values.
    file.write(f"# Special Numeric Values\n")
    special_values = df[df<0].count()
    file.write(f"{special_values}\n")
