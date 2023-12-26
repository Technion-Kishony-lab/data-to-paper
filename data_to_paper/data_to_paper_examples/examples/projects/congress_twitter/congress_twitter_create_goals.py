from data_to_paper_examples.examples.run_project import get_paper

project_specific_goal_guidelines = """\
* Avoid choosing politically sided goals. \
For example, do NOT choose a goal like "Democrats are more/less engaged than Republicans".

* Avoid choosing the following goal that we have already explored:
- The probability of interaction of a member is associated with their Party, State, and Chamber.
"""

if __name__ == '__main__':
    for jrun in range(15):

        RUN_PARAMETERS = dict(
            project='congress_twitter',
            data_filenames=["congress_members.csv", "congress_edges.dat"],
            research_goal=None,
            should_do_data_exploration=True,
        )

        get_paper(**RUN_PARAMETERS,
                  output_folder=f"open_goal_{jrun}",
                  copy_openai_responses=False,
                  project_specific_goal_guidelines=project_specific_goal_guidelines,
                  should_mock_servers=True,
                  load_from_repo=True,
                  save_on_repo=True)
