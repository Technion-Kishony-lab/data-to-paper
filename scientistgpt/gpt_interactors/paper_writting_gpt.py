import os
from dataclasses import dataclass, field
from typing import Optional

from scientistgpt.gpt_interactors.converser_gpt import PaperWritingGPT
from scientistgpt.gpt_interactors.scientist_gpt import ScientificProducts
from scientistgpt.gpt_interactors.text_extractors import extract_latex_text_from_response
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

    parts_to_write = ['abstract', 'title', 'introduction', 'methods', 'results', 'discussion', 'conclusion']

    def __post_init__(self):
        super().__post_init__()

        self.conversation_manager.create_conversation()
        self._populate_conversation()

    def _populate_conversation(self):
        self.conversation_manager.append_system_message(dedent_triple_quote_str("""
        You are a scientist that able to write full length sound scientific papers.
        Your will:
        1. Write every part of the paper in scientific language, in `.tex` format.
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
        prompt = f"Please write only the {section} of the paper, do not write any other parts yet!" \
                 f"remember to write that in .tex format," \
                 f"don't add any additional commands like the \\begin{{document}} and \\end{{document}}."
        self.conversation_manager.append_user_message(prompt, tag=f'request_{section}')

        assistant_response = self.conversation_manager.get_and_append_assistant_message(tag=f'{section}')
        # extract only the tex content of the assistant and make sure it is correct
        latex_content = self.extract_correct_part_from_response(assistant_response, section)
        setattr(self.scientific_products, section, latex_content)

    def extract_correct_part_from_response(self, response: str, section: str):
        """
        extract the correct part of the response, i.e. the latex content of the response.
        """
        # extract only the tex content of the assistant
        try:
            latex_content = extract_latex_text_from_response(response)
            # check that the response has the right part of the paper
            if section == 'title':
                if not latex_content.startswith('\\title'):
                    raise ValueError(f'Expected to find \\title in the response, but did not find it.')
                # find if there is any other section within the response of the assistant using the \section command
                # if there is, raise an error
                elif '\\section' in latex_content:
                    raise ValueError(f'Expected to find only \\title in the response, but found other parts.')
            elif section == 'abstract':
                if not latex_content.startswith('\\begin{abstract}'):
                    raise ValueError(f'Expected the answer to begin with \\begin{{abstract}} in the response, but did not find it.')
                elif not latex_content.endswith('\\end{abstract}'):
                    raise ValueError(f'Expected the answer to end with \\end{{abstract}} in the response, but did not find it.')
                # find if there is any other section within the response of the assistant using the \section command
                # if there is, raise an error
                elif '\\section' in latex_content:
                    raise ValueError(f'Expected to find only \\begin{{abstract}} in the response, but found other parts.')
            else:
                if not latex_content.startswith(f'\\section{{{section}}}'):
                    raise ValueError(f'Expected the answer to begin with \\section{{{section}}} in the response, but did not find it.')
        except ValueError as e:
            self.conversation_manager.append_user_message(
                dedent_triple_quote_str("""
                I checked your response and it seems that it does not contain the correct part of the paper.
                The error I got is:
                {}
                Please rewrite the {section} again with the error fixed.
                """).format(str(e)), section)
            # TODO: fix the logic of message recreation
            latex_content = self.conversation_manager.get_and_append_assistant_message(tag=f'{section}')
        return latex_content

    def write_paper_step_by_step(self):
        """
        write the paper section by section, after each section restart conversation to the abstract.
        """
        # write the abstract
        self.write_paper_section('abstract')
        # write the rest of the paper
        for section in ['title', 'introduction', 'methods', 'results', 'discussion', 'conclusion']:
            self.write_paper_section(section)
            self.conversation_manager.reset_back_to_tag('abstract')

    def assemble_paper(self):
        """
        assemble the paper from the different sections.
        """
        with open(self.paper_template_filename, 'r') as f:
            paper_template = f.read()
        # replace each section with the corresponding section, in the paper template the sections are marked with
        # @@@section_name@@@
        for section in self.parts_to_write:
            paper_template = paper_template.replace(f'@@@{section}@@@', getattr(self.scientific_products, section))
        # write the paper to a file
        with open(self.paper_filename, 'w') as f:
            f.write(paper_template)
        # compile the paper
        os.system(f'pdflatex {self.paper_filename}')

    def write_paper(self):
        self.write_paper_step_by_step()
        self.assemble_paper()

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
