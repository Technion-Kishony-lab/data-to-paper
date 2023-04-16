import os
from dataclasses import dataclass, field
from typing import Optional

from scientistgpt.gpt_interactors.converser_gpt import PaperWritingGPT
from scientistgpt.gpt_interactors.scientific_products import ScientificProducts
from scientistgpt.utils import dedent_triple_quote_str

MAX_SECTION_RECREATION_ATTEMPTS = 3


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

    # scientific_products is a field that cannot stay None
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
        4. Do not cite any papers.
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
        prompt = f"Please write only the {section} of the paper, do not write any other parts! " \
                 f"remember to write that in .tex format including any math or symbols that needs escapes! " \
                 f"don't add \\begin{{document}} and \\end{{document}} commands as I will add them manually."
        self.conversation_manager.append_user_message(prompt, tag=f'request_{section}')
        latex_content = None
        max_attempts = MAX_SECTION_RECREATION_ATTEMPTS
        for attempt in range(max_attempts):
            try:
                assistant_response = self.conversation_manager.get_and_append_assistant_message(tag=f'{section}')
                # extract only the tex content of the assistant and make sure it is correct
                latex_content = self.extract_correct_part_from_response(assistant_response, section)
            except ValueError as e:
                self.comment(f"The {section} was not written correctly, trying again, attempt "
                             f"{attempt + 1} out of {max_attempts}")
                self.conversation_manager.append_user_message(
                    dedent_triple_quote_str("""
                    I checked your response and it seems that it does not contain the correct part of the paper 
                    or that there is problem with the latex formatting.
                    The error I got is:

                    {}

                    Please rewrite the {} part completely again with the error fixed.
                    """).format(str(e), section))
            except Exception as e:
                self.comment(f"There was unknown problem in creating {section}, trying again, attempt "
                             f"{attempt + 1} out of {max_attempts}")
                self.conversation_manager.append_user_message(
                    dedent_triple_quote_str("""
                    I checked your response and it seems that there is problem with the section you created.
                    The error I got is:

                    {}

                    Please rewrite the {} part completely again with the error fixed.
                    """).format(str(e), section))
            else:
                # no error was raised, save the content of the section
                self.comment(f"{section} section of the paper successfully created.")
                setattr(self.scientific_products, section, latex_content)
                return latex_content
        if latex_content is None:
            # if we got here, it means that we failed to create the section
            self.comment(f"Failed to create the {section} section of the paper after {max_attempts} attempts.")
            return False

    @staticmethod
    def extract_correct_part_from_response(response: str, section: str):
        """
        extract the correct part of the response, i.e. the latex content of the response.
        """
        # extract only the tex content of the assistant
        # latex_content = extract_latex_text_from_response(response).strip()
        # check that the response has the right part of the paper
        if section == 'title':
            try:
                title = response.split('\\title{')[1].split('}')[0]
                if title == '':
                    raise ValueError(f'I got an empty title.')
                latex_content = '\\title{' + title + '}'
            except Exception:
                raise ValueError(f'Expected to find \\title in the response, but did not find it.')
            # find if there is any other section within the response of the assistant using the \section command
            # if there is, raise an error
            # elif '\\section' in latex_content:
            #     raise ValueError(f'Expected to find only \\title in the response, but found other parts.')
        elif section == 'abstract':
            try:
                abstract = response.split('\\begin{abstract}')[1].split('\\end{abstract}')[0]
                if abstract == '':
                    raise ValueError(f'I got an empty abstract.')
                latex_content = '\\begin{abstract}' + abstract + \
                                '\\end{abstract}'
            except Exception:
                raise ValueError(f'Expected to find \\begin{{abstract}} and \\end{{abstract}} in the response, '
                                 f'but did not find it.')
            # if not latex_content.startswith('\\begin{abstract}'):
            #     raise ValueError(
            #         'Expected the answer to begin with \\begin{abstract} in the response, but did not find it.')
            # elif not latex_content.endswith('\\end{abstract}'):
            #     raise ValueError(
            #         'Expected the answer to end with \\end{abstract} in the response, but did not find it.')
            # find if there is any other section within the response of the assistant using the \section command
            # if there is, raise an error
            # elif '\\section' in latex_content:
            #     raise ValueError(
            #         'Expected to find only \\begin{abstract} and \\end{abstract} in the response, but found other '
            #         'sections.')
        else:
            try:
                section_content = response.split(f'\\section{{{section.capitalize()}}}')[1]
                if section_content == '':
                    raise ValueError(f'I got an empty {section} section.')
                latex_content = f'\\section{{{section.capitalize()}}}' + section_content
            except Exception:
                raise ValueError(
                    f'Expected to find \\section{{{section.capitalize()}}} in the response, but did not find it.')
            # if not latex_content.startswith(f'\\section{{{section.capitalize()}}}'):
            #     raise ValueError(
            #         f'Expected the answer to begin with \\section{{{section.capitalize()}}} in the response, but did '
            #         f'not find it.')
            # find if there is any other section within the response of the assistant using the \section command
        return latex_content

    def write_paper_step_by_step(self):
        """
        write the paper section by section, after each section restart conversation to the abstract.
        """
        # write the abstract
        self.write_paper_section('abstract')
        self.conversation_manager.reset_back_to_tag('ready_to_abstract')
        abstract_prompt = dedent_triple_quote_str("""
        The abstract of the paper is:

        {}

        """).format(self.scientific_products.abstract)
        self.conversation_manager.append_user_message(abstract_prompt, tag='abstract_written')
        # write the rest of the paper
        for section in ['title', 'introduction', 'methods', 'results', 'discussion', 'conclusion']:
            self.write_paper_section(section)
            self.conversation_manager.reset_back_to_tag('abstract_written')

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
