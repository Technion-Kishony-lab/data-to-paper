from queries import data_description, goal_description

from scientistgtp import ScientistGTP, ANALYSIS_PLAN

runner = ScientistGTP(run_plan=ANALYSIS_PLAN,
                      data_description=data_description,
                      goal_description=goal_description)

runner.run_all(annotate=True)
