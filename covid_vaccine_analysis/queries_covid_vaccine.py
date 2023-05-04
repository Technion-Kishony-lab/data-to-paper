# flake8: noqa

from typing import List

from g3pt.base_steps.types import DataFileDescriptions, DataFileDescription
from g3pt.utils import dedent_triple_quote_str


data_file_descriptions: DataFileDescriptions = DataFileDescriptions([
    DataFileDescription(
        file_path='eng_covid_vaccine_side_effects.csv',
        description=dedent_triple_quote_str("""
            a csv file containing information about reports of side effects followed by vaccine
            that were reported by medical staff in israel, the vaccine that was given is "Pfizer BioNTech (BNT162b2) COVID-19 vaccine".
            Each line indicates a side effect event where a patient was reported to have an effect event after vaccination. 
            
            The file has 6 columns: 
            #1 PortionNum - the number of portion of the vaccine, 1, 2, 3 or 4
            #2 SideEffectStartTime - number of units of time that passed since the vaccination was administered, 999 means 'continuous'
            #3 DetailsStartTimeType - the type of unit of time that passed since the vaccination was administered (minutes, hours, days, weeks, months, NaN)
            #4 SideEffectDurationTime - number of units of time that passed since the side effect was affecting the patient, 999 means 'continuous'
            #5 DetailsDurationTimeType - the type of unit of time that passed since the side effect was affecting the patient (minutes, hours, days, weeks, continuous, NaN)
            #6 Effect - the side effect that was reported by the medical staff""")),
])

research_goal = """
The primary objective of this research is to explore the differences in side effects among doses, as indicated by the portion numbers. The research questions to address include:
Are there differences in the frequency and severity of side effects across different portion numbers? This will help determine if certain treatment groups or doses exhibit a higher likelihood of specific side effects compared to others.
Are there unique side effects associated with specific portion numbers? Identifying side effects that are unique to a particular treatment group or dose can provide insights into potential differences in their mechanisms of action or safety profiles.
How do the onset times and durations of side effects vary across portion numbers?
Are there any trends or patterns in the occurrence of side effects across increasing or decreasing portion numbers? Identifying trends in side effect profiles can inform the development of treatment strategies to minimize side effects or optimize the benefit-risk balance.
"""
