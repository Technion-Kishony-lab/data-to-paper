

# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'Intercept': (None, 'The value of the predicted response when all independent variables are 0'),
 'Party_Code_From': ('SrcParty', 'Political party of the tweeting congress member'),
 'Party_Code_To': ('TgtParty', 'Political party of the tweeted-at congress member'),
 'Chamber_Code_From': ('SrcChamber', 'Chamber of the tweeting congress member'),
 'Chamber_Code_To': ('TgtChamber', 'Chamber of the tweeted-at congress member'),
 'Coeff.': ('Coefficient', 'Estimated parameter of the logistic regression model'),
 'Std.Err.': ('StdErr', 'Standard error of the estimated parameter'),
 'z': ('Z-Score', 'Value of the test statistic for hypotheses testing of individual parameter estimates'),
 'P>|z|': ('P-Value', 'Twotailed probability of getting a test statistic as extreme as, or more extreme than, the observed value under the null hypothesis'),
 '[0.025': ('CI-Lower', 'Lower limit of the 95% confidence interval'),
 '0.975]': ('CI-Upper', 'Upper limit of the 95% confidence interval')
}

# TABLE 1
df = pd.read_pickle('table_1.pkl')
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
 False: ('DiffPartyCham', 'Interactions between members of different party or Chamber'),
 True: ('SamePartyCham', 'Interactions between members of the same party and Chamber'),
 'R_House': ('R-House', None),
 'D_House': ('D-House', None),
 'D_Senate': ('D-Senate', None),
 'I_Senate': ('I-Senate', None),
 'R_Senate': ('R-Senate', None),
 'Party_From': ('Source Party', None),
 'Chamber_From': ('Source Chamber', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(index=abbrs_to_names, columns=abbrs_to_names, inplace=True)

to_latex_with_note(
 df, 'table_1.tex',
 caption='Number of Twitter interactions between Congress members by Party, Chamber, and whether they interacted with members of the same or a different party and chamber.',
 label='table:interaction_counts_within_across_party_chamber',
 note=None,
 legend=legend
 )

# TABLE 2
df = pd.read_pickle('table_2.pkl')
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
 'Party_Code_From': ('SrcParty', 'Political party affiliation of the tweeting member'),
 'Chamber_Code_From': ('SrcChamber', 'Chamber (House or Senate) of the tweeting member'),
}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(index=abbrs_to_names, columns=abbrs_to_names, inplace=True)
df['P-Value'] = df['P-Value'].apply(format_p_value)

to_latex_with_note(
 df, 'table_2.tex',
 caption='Logistic regression model for the likelihood of Twitter interaction between Congress members based on their partisanship and chamber association.',
 label='table:logit_model_fixtures',
 note=None,
 legend=legend
 )
