
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'Sex': ('Sex', '0: Female, 1: Male'),
 'Age': ('Age', 'Patient age (years, rounded to half years)'),
 'Height': ('Height', 'Patient height (cm)'),
 'Weight': ('Weight', 'Patient weight (kg)'),
 'OTTD': ('OTTD', 'Optimal Tracheal Tube Depth as determined by chest X-ray (in cm)'),
 'MSE': ('MSE', 'Mean Squared Error'),
 'ElasticNet': ('Elastic Net', 'A linear regression model trained with L1 and L2-norm regularization of the coefficients'),
 'MLP': ('Multilayer Perceptron', 'A class of feedforward artificial neural network'),
 'SVR': ('Support Vector Regression', 'A type of Support vector machine that supports linear and non-linear regression.'),
 'Random Forest': ('Random Forest', 'A meta estimator that fits a number of classifying decision trees on various sub-samples of the dataset and uses averaging to improve the predictive accuracy and control over-fitting.'),
}

# TABLE 1
df1 = pd.read_pickle("table_1.pkl")

# RENAME ROWS AND COLUMNS
mapping_table1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
abbrs_to_names, legend = split_mapping(mapping_table1)
df1 = df1.rename(index=abbrs_to_names)

# Save as Latex file
to_latex_with_note(
 df1, 
 'table_1.tex', 
 caption="Comparison of Mean Squared Error (MSE) between ML models and formula-based models", 
 label="table:comparison_mse",
 note="In the model names, 'Random Forest', 'Elastic Net', 'Support Vector Regression', and 'Multilayer Perceptron' refer to machine learning models while 'Height Model', 'Age Model', and 'Tube ID Model' refer to formula-based models.",
 legend=legend)

# The legend argument now includes 'Elastic Net' as well. All abbreviations are now properly referenced in the legend.
