from data_to_paper_examples.examples.run_project import get_paper

goal = "Research Goal:\n" \
       "To construct and test a prediction model for optimal tracheal tube depth (tube_depth_G) in pediatric patients " \
       "using machine learning based on the variables age, sex, height, weight. The tracheal tube depth is appropriate " \
       "when the tracheal tube tip is located between the upper margin of T1 and the lower margin of T3. The optimal " \
       "position is defined as the mean of these 2 values.\n" \
       "Hypothesis:'n" \
       "- Different machine learning models can be used to predict the optimal tracheal tube depth. Machine learning " \
       "models to test are random forest, elastic net, support vector machine, and artificial neural network. \n" \
       "- Machine learning models perform better than the commonly used formula-based methods, which are based on age, " \
       "height, and tracheal tube internal diameter, i.d. i) the height based method " \
       "(tube depth [cm] = height [cm] / 10 + 5) , ii) age based methods " \
       "(9 cm for those aged 0–6 months, 10 cm for those aged 6–12 months, and 11 cm for those aged under 2 years, " \
       "and the cardiac life support formula (tube depth [cm] = 12 + age [years] / 2) for those above 2 years and " \
       "iii) tube internal diameter based method (tube depth [cm] =3 x (tube ID))",

RUN_PARAMETERS = dict(
    project="t_tube_insertion",
    data_filenames=["tracheal_tube_insertion.csv"],
    research_goal=goal,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    get_paper(**RUN_PARAMETERS,
              output_folder="paper1",
              should_mock_servers=True,
              load_from_repo=True,
              save_on_repo=True)
