
# IMPORT
import pandas as pd
from my_utils import df_to_latex, df_to_figure, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES AND FIGURES
# Define mapping for all df labels that need to be renamed and/or glossary defined.
all_mapping: AbbrToNameDef = {
    'Diabetes_binary': ('Diabetes', '1: Yes, 0: No - Presence of Diabetes'),
    'HighBP': ('High Blood Pressure', '1: Yes, 0: No - Presence of High Blood Pressure'),
    'HighChol': ('High Cholesterol', '1: Yes, 0: No - Presence of High Cholesterol'),
    'CholCheck': ('Cholesterol Check', '1: Yes, 0: No - Cholesterol check in the last 5 years'),
    'BMI': ('Body Mass Index (BMI)', 'Body Mass Index calculated from weight and height'),
    'Smoker': ('Smoker', '1: Yes, 0: No - Smoking status'),
    'Stroke': ('Stroke', '1: Yes, 0: No - History of Stroke'),
    'HeartDiseaseorAttack': ('Heart Disease/Attack', '1: Yes, 0: No - Presence of coronary heart disease or myocardial infarction'),
    'PhysActivity': ('Physical Activity', '1: Yes, 0: No - Engaged in physical activity in the past 30 days'),
    'Fruits': ('Fruits Consumption', '1: Yes, 0: No - Consumed one or more fruits each day'),
    'Veggies': ('Vegetable Consumption', '1: Yes, 0: No - Consumed one or more vegetables each day'),
    'HvyAlcoholConsump': ('Heavy Alcohol Consumption', '1: Yes, 0: No - Heavy drinkers'),
    'AnyHealthcare': ('Healthcare Coverage', '1: Yes, 0: No - Any kind of health care coverage'),
    'NoDocbcCost': ('Unmet Medical Need Due to Cost', '1: Yes, 0: No - Needed to see a doctor but could not because of cost in the past 12 months'),
    'GenHlth': ('General Health', 'Self-reported health status (1=excellent, 2=very good, 3=good, 4=fair, 5=poor)'),
    'MentHlth': ('Mental Health (Days)', 'Number of days in the past 30 days mental health was not good'),
    'PhysHlth': ('Physical Health (Days)', 'Number of days in the past 30 days physical health was not good'),
    'DiffWalk': ('Difficulty Walking', '1: Yes, 0: No - Serious difficulty walking or climbing stairs'),
    'Sex': ('Sex', '0: Female, 1: Male - Participant sex'),
    'Age': ('Age Group', 'Age group categories (1= 18 - 24, 2= 25 - 29, ..., 12= 75 - 79, 13 = 80 or older)'),
    'Education': ('Education Level', 'Education level on a scale of 1 to 6 (1=Never attended school, 2=Elementary, 3=Some high school, 4=High school, 5=Some college, 6=College)'),
    'Income': ('Income Level', 'Income scale on a scale of 1 to 8 (1= <=10K, 2= <=15K, 3= <=20K, 4= <=25K, 5= <=35K, 6= <=50K, 7= <=75K, 8= >75K)'),

    # Specific terms for logistic regression and interaction results
    'Intercept': (None, 'Intercept term in the logistic regression model'),
    'PhysActivity:Fruits': ('PA*Fruit', 'Interaction term between Physical Activity and Fruits Consumption'),
    'PhysActivity:Veggies': ('PA*Veggie', 'Interaction term between Physical Activity and Vegetable Consumption'),
    'PhysActivity:Smoker': ('PA*Smoker', 'Interaction term between Physical Activity and Smoking Status'),
    'Fruits:Veggies': ('Fruit*Veggie', 'Interaction term between Fruits and Vegetable Consumption'),
    'Fruits:Smoker': ('Fruit*Smoker', 'Interaction term between Fruits Consumption and Smoking Status'),
    'Veggies:Smoker': ('Veggie*Smoker', 'Interaction term between Vegetable Consumption and Smoking Status'),
    'PhysActivity:Fruits:Veggies': ('PA*Fruit*Veggie', 'Three-way interaction term among Physical Activity, Fruits, and Vegetable Consumption'),
    'PhysActivity:Fruits:Smoker': ('PA*Fruit*Smoker', 'Three-way interaction term among Physical Activity, Fruits Consumption and Smoking Status'),
    'PhysActivity:Veggies:Smoker': ('PA*Veggie*Smoker', 'Three-way interaction term among Physical Activity, Vegetable Consumption and Smoking Status'),
    'Fruits:Veggies:Smoker': ('Fruit*Veggie*Smoker', 'Three-way interaction term among Fruits, Vegetable Consumption and Smoking Status'),
    'PhysActivity:Fruits:Veggies:Smoker': ('PA*Fruit*Veg*Smoker', 'Four-way interaction term among Physical Activity, Fruits, Vegetable Consumption and Smoking Status'),

    # Define common abbreviations
    'ci': ('CI', '95% Confidence Interval'),
    'p_value': ('P-value', 'P-values indicating the significance of the coefficient'),
    'z': ('z', 'Z-statistic for the hypothesis test that the coefficient is zero'),
}

## Process df_desc_stat:
df_desc_stat = pd.read_pickle('df_desc_stat.pkl')
# Remove column 'count' after asserting there is only one unique value
count_unique = df_desc_stat["count"].unique()
assert len(count_unique) == 1
df_desc_stat.drop(columns=["count"], inplace=True)

# Rename columns and rows:
mapping = dict((k, v) for k, v in all_mapping.items() if is_str_in_df(df_desc_stat, k))
abbrs_to_names, glossary = split_mapping(mapping)
df_desc_stat.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)

df_to_latex(
    df_desc_stat, 'df_desc_stat_formatted',
    caption="Descriptive statistics of selected variables in the BRFSS 2015 dataset",
    note=f"Note: For all rows, the count is {count_unique[0]}.",
    glossary=glossary)

## Process df_log_reg:
df_log_reg = pd.read_pickle('df_log_reg.pkl')

# Remove 'Intercept' row 
df_log_reg = df_log_reg.drop(index=['Intercept'])

# Rename columns and rows:
mapping = dict((k, v) for k, v in all_mapping.items() if is_str_in_df(df_log_reg, k))
abbrs_to_names, glossary = split_mapping(mapping)
df_log_reg.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)

# Adding missing labels to glossary
glossary.update({
    'PA*Fruit': 'Interaction term between Physical Activity and Fruits Consumption',
    'PA*Fruit*Smoker': 'Three-way interaction term among Physical Activity, Fruits Consumption and Smoking Status',
    'PA*Fruit*Veg*Smoker': 'Four-way interaction term among Physical Activity, Fruits, Vegetable Consumption and Smoking Status',
    'PA*Fruit*Veggie': 'Three-way interaction term among Physical Activity, Fruits, and Vegetable Consumption',
    'PA*Smoker': 'Interaction term between Physical Activity and Smoking Status',
    'PA*Veggie': 'Interaction term between Physical Activity and Vegetable Consumption',
    'PA*Veggie*Smoker': 'Three-way interaction term among Physical Activity, Vegetable Consumption and Smoking Status',
})

df_to_latex(
    df_log_reg, 'df_log_reg_formatted',
    caption="Logistic regression results for the association between lifestyle factors and Diabetes, adjusted for confounders",
    glossary=glossary,
    note="Coef. = Coefficient; Std.Err. = Standard Error; P>|z| = P-value for Z-statistic. Interaction terms are denoted as PA (Physical Activity), Fruit (Fruits Consumption), Veggie (Vegetable Consumption), and Smoker.")

## Process df_interactions:
df_interactions = pd.read_pickle('df_interactions.pkl')

# Rename columns and rows:
mapping = dict((k, v) for k, v in all_mapping.items() if is_str_in_df(df_interactions, k))
abbrs_to_names, glossary = split_mapping(mapping)
df_interactions.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)

df_to_figure(
    df_interactions, 'df_interactions_formatted',
    caption="Interaction effects of lifestyle factors on Diabetes", 
    glossary=glossary,
    kind='bar',
    y=['Coef.'],
    y_ci=['CI'],
    y_p_value=['P-value'],
    ylabel="Coefficient",
)

## Process df_lifestyle_combined:
df_lifestyle_combined = pd.read_pickle('df_lifestyle_combined.pkl')

# Rename columns and rows:
mapping = dict((k, v) for k, v in all_mapping.items() if is_str_in_df(df_lifestyle_combined, k))
abbrs_to_names, glossary = split_mapping(mapping)
df_lifestyle_combined.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)

df_to_figure(
    df_lifestyle_combined, 'df_lifestyle_combined_formatted',
    caption="Combined effects of lifestyle factors (physical activity, fruit and vegetable consumption, and smoking) on Diabetes", 
    glossary=glossary,
    kind='bar',
    y=['coef'],
    y_ci=['CI'],
    y_p_value=['P-value'],
    ylabel="Coefficient",
)
