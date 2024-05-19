from data_to_paper.base_cast.types import Profile, Algorithm


Performer = Profile(
    agent_name='Performer',
    name='Sheldon',
    title='me!',
    description='',
    image_file='',
    algorithm=Algorithm.GPT,
)

Director = Profile(
    agent_name='Director',
    name='USER',
    title='director',
    description='',
    image_file='',
    algorithm=Algorithm.PRE_PROGRAMMED,
)

DataExplorer = Profile(
    agent_name='DataExplorer',
    name='Lenny',
    title='data explorer',
    description='',
    image_file='',
    algorithm=Algorithm.PRE_PROGRAMMED,
)

GoalReviewer = Profile(
    agent_name='GoalReviewer',
    name='Prof. Proton',
    title='goal reviewer',
    description='',
    image_file='',
    algorithm=Algorithm.PRE_PROGRAMMED,
)

DataPreprocessor = Profile(
    agent_name='DataPreprocessor',
    name='Leslie',
    title='data preprocessor',
    description='',
    image_file='',
    algorithm=Algorithm.PRE_PROGRAMMED,
)

PlanReviewer = Profile(
    agent_name='PlanReviewer',
    name='Amy',
    title='research plan reviewer',
    description='',
    image_file='',
    algorithm=Algorithm.GPT,
)

Debugger = Profile(
    agent_name='Debugger',
    name='Raj',
    title='debugger',
    description='',
    image_file='',
    algorithm=Algorithm.PRE_PROGRAMMED,
)

InterpretationReviewer = Profile(
    agent_name='InterpretationReviewer',
    name='Bernie',
    title='interpretation reviewer',
    description='',
    image_file='',
    algorithm=Algorithm.GPT,
)

Writer = Profile(
    agent_name='Writer',
    name='Penny',
    title='scientific writer',
    description='',
    image_file='',
    algorithm=Algorithm.GPT,
)

CitationExpert = Profile(
    agent_name='CitationExpert',
    name='Stewie',
    title='Great with literature citations',
    description='',
    image_file='',
    algorithm=Algorithm.GPT,
)

TableExpert = Profile(
    agent_name='TableExpert',
    name='Howie',
    title='Data-presentation expert',
    description='',
    image_file='',
    algorithm=Algorithm.GPT,
)
