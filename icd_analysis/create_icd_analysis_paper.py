from queries import data_description, goal_description

from scientistgpt import ScientistGPT, ScientistGPT_ANALYSIS_PLAN


SAVE_AS = 'icd_data2paper_1.txt'

runner = ScientistGPT(run_plan=ScientistGPT_ANALYSIS_PLAN,
                      data_description=data_description,
                      goal_description=goal_description)

runner.run_all(annotate=True)

runner.conversation.save(SAVE_AS)
