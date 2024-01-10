
import pandas as pd
import numpy as np

# Load the data
data = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# Replace NaN and infinite values with NaN.
data = data.replace([np.inf, -np.inf], np.nan)

# Open the output file
with open('data_exploration.txt', 'w') as file:
    # Data Size
    file.write("# Data Size\n")
    file.write(f"Number of rows: {data.shape[0]}\n")
    file.write(f"Number of columns: {data.shape[1]}\n\n")

    # Summary Statistics
    file.write("# Summary Statistics\n")
    with pd.option_context('display.max_rows', None):
        file.write(f"{data.describe(include='all').round(2)}\n\n")

    # Categorical Variables
    file.write("# Categorical Variables\n")
    cat_vars = data.select_dtypes(include=['object']).columns
    for cat in cat_vars:
        file.write(f"\n*** Variable: {cat} ***\n")
        val_count = data[cat].value_counts(dropna=False).to_string()
        file.write(f"{val_count}\n\n")

    # Average of 'ProlongedRupture' excluding NaN.
    if not data['ProlongedRupture'].isnull().values.any():
        file.write("# Average ProlongedRupture excluding NaN\n")
        file.write(f"Average ProlongedRupture: {data['ProlongedRupture'].mean():.2f}\n\n")

    # Average of 'SNAPPE_II_SCORE' excluding NaN.
    if not data['SNAPPE_II_SCORE'].isnull().values.any():
        file.write("# Average SNAPPE_II_SCORE excluding NaN\n")
        file.write(f"Average SNAPPE_II_SCORE: \
        {data['SNAPPE_II_SCORE'].mean():.2f}\n\n")

    # Missing Values
    file.write("# Missing Values\n")
    missing_values = data.isnull().sum()
    missing_values_pct = (missing_values / data.shape[0]).apply(lambda x: f'{x:.2%}')
    missing_values = missing_values[missing_values != 0].astype(str)
    missing_values_pct = missing_values_pct[missing_values_pct != '0.00%']
    missing_values_df = pd.concat([missing_values, missing_values_pct], axis=1,
                                  keys=['Total Missing', 'Percent Missing'])
    file.write(f"{missing_values_df}\n")
