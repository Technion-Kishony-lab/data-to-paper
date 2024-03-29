from data_to_paper_examples.examples.run_project import get_paper, get_output_path


generic_dirname = "open_goal_accum_{}"


def read_goal_and_hypothesis(folder):
    with open(folder / 'goal.txt') as f:
        goal = f.read()
    return goal.split('Here is our Research Goal')[1].split('Here is our Hypothesis Testing Plan')[0].strip()


def get_output_path_for_num(num):
    return get_output_path(project=project, output_folder=generic_dirname.format(num), save_on_repo=True)


project = 'congress_twitter'


if __name__ == '__main__':
    for jrun in range(4,5):
        project_specific_goal_guidelines = \
            '* Avoid choosing politically sided goals. ' \
            'For example, do NOT choose a goal like "Democrats are more/less engaged than Republicans"\n\n'

        if jrun > 0:
            project_specific_goal_guidelines += \
                f"* Avoid choosing the following {jrun} goals that we have already explored:\n"
            for j in range(jrun):
                goal = read_goal_and_hypothesis(get_output_path_for_num(j))
                project_specific_goal_guidelines += f"({j + 1})\n{goal}\n\n"

        RUN_PARAMETERS = dict(
            project=project,
            data_filenames=["congress_members.csv", "congress_edges.dat"],
            research_goal=None,
            should_do_data_exploration=True,
        )

        get_paper(**RUN_PARAMETERS,
                  output_folder=generic_dirname.format(jrun),
                  copy_openai_responses=False,
                  project_specific_goal_guidelines=project_specific_goal_guidelines,
                  should_mock_servers=True,
                  load_from_repo=True,
                  save_on_repo=True)
