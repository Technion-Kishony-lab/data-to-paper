from scientistgpt.cast.types import Profile


Student = Profile(
    agent_name='Student',
    name='Sheldon',
    title='me!',
    description='Hello, my name is Sheldon Cooper. '
                'I am trying to become a scientist, do research and write a scientific paper.',
    image_file='sheldon.png',
)

Mentor = Profile(
    agent_name='Mentor',
    name='Dr. Eric Gablehauser',
    title='my mentor',
    description='Hello, my name is Dr. Eric Gablehauser. '
                'I am a professor of physics at Caltech. '
                'I am here to help Sheldon with his research.',
    image_file='eric.png',
)

PlanReviewer = Profile(
    agent_name='PlanReviewer',
    name='Dr. Arthur Jeffries',
    title='research plan reviewer',
    description='Hello, my name is Dr. Arthur Jeffries. '
                'I am a professor of physics at Caltech. '
                'I am here to help review Sheldon\'s research plan.',
    image_file='arthur.png',
)

Secretary = Profile(
    agent_name='Secretary',
    name='Penny',
    title='administrative assistant',
    description='Hello, my name is Penny. '
                'I am here to help Sheldon with any small stuff he might need.',
    image_file='penny.png',
)

Debugger = Profile(
    agent_name='Debugger',
    name='Howard Wolowitz',
    title='debugger',
    description='Hello, my name is Howard Wolowitz. '
                'I am a physicist and a friend of Sheldon\'s. '
                'I am here to help debug Sheldon\'s code.',
    image_file='howard.png',
)

Writer = Profile(
    agent_name='Writer',
    name='Dr. Amy Farrah Fowler',
    title='scientific writer',
    description='Hello, my name is Dr. Amy Farrah Fowler. '
                'I am a neurobiologist and a friend of Sheldon\'s. '
                'I am here to help Sheldon write his scientific paper.',
    image_file='amy.png',
)

LiteratureReviewer = Profile(
    agent_name='LiteratureReviewer',
    name='Dr. Raj Koothrappali',
    title='literature reviewer expert',
    description='Hello, my name is Dr. Raj Koothrappali. '
                'I am a theoretical physicist and a friend of Sheldon\'s. '
                'I am here to help Sheldon review the literature.',
    image_file='raj.png',
)

Director = Profile(
    agent_name='Director',
    name='{}',
    title='director',
    description='Hi everyone!\n'
                'I am just here to observe the future and see how multi-role gpt-driven characters can carry.\n'
                'a complex task on their own by interacting and helping each other.\n\n'
                'I am also the one who gave the data to Sheldon and am looking forward to see how he analyzes it.',
    image_file='anonymous_user.png',
)
