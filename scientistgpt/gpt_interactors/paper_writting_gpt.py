from dataclasses import dataclass, field
from typing import Optional

from scientistgpt.gpt_interactors.converser_gpt import PaperWritingGPT
from scientistgpt.gpt_interactors.scientist_gpt import ScientificProducts
from scientistgpt.utils import dedent_triple_quote_str


@dataclass
class PaperAuthorGPT(PaperWritingGPT):
    """
    Interact with chatgpt to write a scientific paper.

    the context we need for the paper writing process is:
    - data description
    - goal description
    - analysis plan
    - analysis results description
    - implications of results
    - limitations of results

    the paper writing process is:
    - write an abstract
    - add abstract to the context, i.e. conversation
    - write an introduction
    - write a methods section
    - write a results section
    - write a discussion section
    - create figures supporting the results
    - write a conclusion
    """
    agent: str = 'Author'
    # set conversation names:
    conversation_name: str = 'pre_paper_conversation'

    scientific_products: Optional[ScientificProducts] = field(default_factory=ScientificProducts)

    def __post_init__(self):
        super().__post_init__()

        self.conversation_manager.create_conversation()
        self._populate_conversation()

    def _populate_conversation(self):
        self.conversation_manager.append_system_message(dedent_triple_quote_str("""
        You are a scientist that able to write sound scientific papers.
        Your will need to:
        1. Write every part of the paper in scientific language in `.tex` format.
        2. Write the paper section by section.
        3. Write the paper in a way that is consistent with the scientific products you have.
        """))
        for tag in ['data_description', 'goal_description', 'analysis_plan',
                    'result_summary', 'implications', 'limitations']:
            prompt = dedent_triple_quote_str("""
            This is the {} part:
            
            {}
            
            """).format(tag, getattr(self.scientific_products, tag))
            self.conversation_manager.append_user_message(prompt, tag=f'adding {tag} to pre_paper_conversation')
            self.conversation_manager.append_surrogate_message(content=f'Great! I now know about the {tag}.')
        self.conversation_manager.append_surrogate_message('I have everything I need to start writing the different '
                                                           'sections of the paper.', tag='ready_to_abstract')

    def write_paper_section(self, section: str):
        prompt = f"Please write the {section} section of the paper."
        self.conversation_manager.append_user_message(prompt, tag=f'request_{section}')

        assistant_response = self.conversation_manager.get_and_append_assistant_message(tag=f'{section}')
        setattr(self.scientific_products, section, assistant_response)



    # conversation_name: str = 'pre_paper_conversation'

    # def __post_init__(self):
    #     super().__post_init__()
    #     self._initialize_pre_paper_conversation()
    #
    # def _initialize_pre_paper_conversation(self):
    #     self.conversation_manager.create_conversation()
    #     self.conversation_manager.append_system_message('Preparing the pre-paper conversation ...')
    #     self.conversation_manager.copy_messages_from_another_conversations()
    #     self.conversation_manager.('Preparing the pre-paper conversation ...', message_callback=self.message_callback)
    #     paper_conversation = Conversation()
    #     paper_conversation.append_message(role=Role.SYSTEM,
    #                                       message='You are a helpful scientist that able to write scientific papers.')
    #     paper_conversation.append_user_message('This is the data description\n\n' + self.data_description)
    #     paper_conversation.append_assistant_message('acknowledged')
    #     paper_conversation.append_user_message('This is the research goal description\n\n' + self.goal_description)
    #     paper_conversation.append_assistant_message('acknowledged')
    #     paper_conversation.append_user_message('This is the analysis plan description\n\n' + self.analysis_plan)
    #     paper_conversation.append_assistant_message('acknowledged')
    #     paper_conversation.append_user_message('This is the analysis results description\n\n' + self.results_summary)
    #     paper_conversation.append_assistant_message('acknowledged')
    #     print_red('Pre-paper conversation is ready! Let\'s write the paper ...', message_callback=self.message_callback)
    #     self.pre_paper_conversation = paper_conversation
    #
    #
    # def write_paper(self):
    #     prompt = dedent_triple_quote_str("""
    #     Write paper - write abstract, introduction, methods, results, discussion and acknowledgments.
    #     Use markdown to format the paper.
    #     In addition you are required to state where to enter the figure of you created during the analysis by using
    #     FIGURE@#@ name_of_figure @#@ where name_of_figure is the name of the figure you want to enter.
    #     Add references to the paper if applicable.
    #     """)
    #     self.pre_paper_conversation.append_user_message(prompt)
    #     self.pre_paper_conversation.get_response_from_chatgpt()
    #     paper = self.pre_paper_conversation.get_last_response()
    #     self.conversation.append_user_message(prompt)
    #     self.conversation.append_assistant_message(paper)
    #     # save the paper to file
    #     with open('paper.txt', 'w') as f:
    #         f.write(paper)
