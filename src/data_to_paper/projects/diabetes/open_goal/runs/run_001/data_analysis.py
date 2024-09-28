
# IMPORT
import pandas as pd
import numpy as np
import pickle
import statsmodels.api as sm
import statsmodels.formula.api as smf
from my_utils import df_to_latex, df_to_figure

# LOAD DATA
data = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# For descriptive statistics Table:
## Table df_desc_stat:
caption = "Descriptive statistics of selected variables in the BRFSS 2015 dataset"

selected_columns = ['Diabetes_binary', 'HighBP', 'HighChol', 'CholCheck', 'BMI', 'Smoker', 
                    'Stroke', 'HeartDiseaseorAttack', 'PhysActivity', 'Fruits', 'Veggies', 
                    'HvyAlcoholConsump', 'AnyHealthcare', 'NoDocbcCost', 'GenHlth', 'MentHlth', 
                    'PhysHlth', 'DiffWalk', 'Sex', 'Age']

desc_stat = data[selected_columns].agg(['count', 'mean', 'std']).transpose()
df_to_latex(desc_stat, 'df_desc_stat', caption=caption)

# PREPROCESSING
# Adjust for confounding variables 
data = pd.get_dummies(data, columns=['Sex', 'Age', 'Education', 'Income'], drop_first=True)

# ANALYSIS

# Hypothesis 1: Lifestyle behaviors and Diabetes (logistic regression)
## Table df_log_reg:
caption = "Logistic regression results for the association between lifestyle factors and Diabetes, adjusted for confounders"
# Assuming unique_columns which corresponds to column names of dummy variables
unique_columns = [col for col in data.columns if col not in ['Diabetes_binary', 'PhysActivity', 'Fruits', 'Veggies', 'Smoker']]

formula = "Diabetes_binary ~ PhysActivity * Fruits * Veggies * Smoker + " + " + ".join(unique_columns)

log_reg_result = sm.Logit.from_formula(formula, data).fit()

# Extracting summary results, limiting to the most relevant rows
terms = ['Intercept', 'PhysActivity', 'Fruits', 'Veggies', 'Smoker', 'PhysActivity:Fruits', 'PhysActivity:Veggies', 'PhysActivity:Smoker', 
         'Fruits:Veggies', 'Fruits:Smoker', 'Veggies:Smoker', 'PhysActivity:Fruits:Veggies', 'PhysActivity:Fruits:Smoker', 'PhysActivity:Veggies:Smoker', 
         'Fruits:Veggies:Smoker', 'PhysActivity:Fruits:Veggies:Smoker']
log_reg_summary = log_reg_result.summary2().tables[1]
df_log_reg = log_reg_summary.loc[log_reg_summary.index.isin(terms)]

df_to_latex(df_log_reg, 'df_log_reg', caption=caption)

## Figure df_interactions:
caption = "Interaction effects of lifestyle factors on Diabetes"

# Extracting interaction results
interaction_terms = ['PhysActivity:Fruits', 'PhysActivity:Veggies', 'PhysActivity:Smoker', 'Fruits:Veggies', 
                     'Fruits:Smoker', 'Veggies:Smoker', 'PhysActivity:Fruits:Veggies', 'PhysActivity:Fruits:Smoker', 
                     'PhysActivity:Veggies:Smoker', 'Fruits:Veggies:Smoker', 'PhysActivity:Fruits:Veggies:Smoker']
interaction_df = df_log_reg.loc[interaction_terms]

# Adding ci and p-value for extraction
interaction_df['ci'] = list(zip(interaction_df['[0.025'], interaction_df['0.975]']))
interaction_df['p_value'] = interaction_df['P>|z|']

df_to_figure(interaction_df, 'df_interactions', caption=caption, kind='bar', 
             y=['Coef.'], y_ci=['ci'], y_p_value=['p_value'])

# Hypothesis 2: Combined effect of lifestyle factors
## Figure df_lifestyle_combined:
caption = "Combined effects of lifestyle factors (physical activity, fruit and vegetable consumption, and smoking) on Diabetes"

# Correcting confounding variables in the formula to include the dummy variables
corrected_columns = [col for col in unique_columns if ':' not in col]
combined_formula = "Diabetes_binary ~ PhysActivity + Fruits + Veggies + Smoker + " + " + ".join(corrected_columns)

combined_logit_model = smf.logit(formula=combined_formula, data=data).fit()
combined_effects = combined_logit_model.summary2().tables[1].loc[['PhysActivity', 'Fruits', 'Veggies', 'Smoker']]

# Creating dataframe for the figure
df_combined_effects = pd.DataFrame({
    'coef': combined_effects['Coef.'],
    'ci': list(zip(combined_effects['[0.025'], combined_effects['0.975]'])),
    'p_value': combined_effects['P>|z|']
})

df_to_figure(df_combined_effects, 'df_lifestyle_combined', caption=caption, kind='bar', 
             y=['coef'], y_ci=['ci'], y_p_value=['p_value'])

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data),
    'Logistic Regression AIC': log_reg_result.aic,
    'Combined Effects Model AIC': combined_logit_model.aic 
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
