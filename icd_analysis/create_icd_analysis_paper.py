from queries import data_description, goal_description

from scientistgpt import ScientistGPT, ScientistGPT_ANALYSIS_PLAN

runner = ScientistGPT(run_plan=ScientistGPT_ANALYSIS_PLAN,
                      data_description=data_description,
                      goal_description=goal_description)

runner.run_all(annotate=True)
