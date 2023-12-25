from data_to_paper_examples.examples.run_project import get_paper

goals = {
    "degree-state_size":
        "Goal: Understand factors affecting the social network in-degree and out-degree of members. \n"
        "Hypothesis: The in-degree and out-degree of a member are associated with the size of their State "
        "(as measured by the number of members in each State), even when controlling for Party and Chamber.\n",

    "degree_inter_state-state_size":
        "Goal: Understand factors affecting the social network inter-state in-degree and out-degree of members. \n"
        "Hypothesis: The in-degree and out-degree of a member are associated with the size of their State "
        "(as measured by the number of members in each State), even when controlling for Party and Chamber, "
        "and even when completely excluding interactions between members from the same State.\n",

    "connectivity-state+chamber+party":
        "Goal: Analyse factors affecting the probability of interaction between members.\n"
        "Hypothesis: The chance that member A engages with member B is associated with:\n"
        "(a) The size of the State of member A (as measured by the number of members in each state).\n"
        "(b) The size of the State of member B.\n"
        "(c) Whether member A and member B are from the same party.\n"
        "(d) Whether member A and member B are from the same Chamber.\n"
        "(e) Whether member A and member B are from the same State.",

    'open-ended': None,
}


project_specific_goal_guidelines = """\
* Avoid choosing politically sided goals. \
For example, do NOT choose a goal like "Democrats are more/less engaged than Republicans".

"""

if __name__ == '__main__':
    for key, goal in list(goals.items())[3:]:
        for jrun in [0]:

            goal = "Goal and Hypothesis:\n" + goal if goal is not None else None

            RUN_PARAMETERS = dict(
                project='congress_twitter',
                data_filenames=["congress_members.csv", "congress_edges.dat"],
                research_goal=goal,
                should_do_data_exploration=True,
            )

            get_paper(**RUN_PARAMETERS,
                      output_folder=f"{key}_{jrun}",
                      copy_openai_responses=True,
                      project_specific_goal_guidelines=project_specific_goal_guidelines,
                      should_mock_servers=True,
                      load_from_repo=True,
                      save_on_repo=True)
