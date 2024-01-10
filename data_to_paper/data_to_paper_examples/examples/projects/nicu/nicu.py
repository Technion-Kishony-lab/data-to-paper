from data_to_paper_examples.examples.run_project import get_paper

goal = """
Research goal: 
Examining the impact of guideline change on neonatal treatment and outcomes.

Hypothesis:
- Change in treatment policy lead to change in treatments.
- The change in treatment policy improved neonatal outcome, measured by duration of stay, apgar scores, etc.
"""

RUN_PARAMETERS = dict(
    project='nicu',
    data_filenames=["meconium_nicu_dataset_preprocessed_short.csv"],
    research_goal=goal,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    for run_name in ['paper2{:02d}'.format(i) for i in range(1, 11)]:
        get_paper(**RUN_PARAMETERS,
                  output_folder=run_name,
                  should_mock_servers=True,
                  load_from_repo=True,
                  save_on_repo=True)
