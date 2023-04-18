import os
from dataclasses import dataclass, field
from typing import Optional

from scientistgpt.gpt_interactors.converser_gpt import PaperWritingGPT
from scientistgpt.gpt_interactors.scientific_products import ScientificProducts, PaperSections, \
    SCIENTIFIC_PRODUCT_FIELD_NAMES, PAPER_SECTION_FIELD_NAMES
from scientistgpt.latex import extract_latex_section_from_response, FailedToExtractLatexContent
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
    conversation_name: str = 'pre_paper_conversation'

    scientific_products: Optional[ScientificProducts] = field(default_factory=ScientificProducts)

    paper_sections: Optional[PaperSections] = field(default_factory=PaperSections)

    def _populate_conversation(self):
        self.conversation_manager.append_system_message(dedent_triple_quote_str("""
        You are a scientist that is able to write full length sound scientific papers.
        Your will:
        1. Write every part of the paper in scientific language, in `.tex` format.
        2. Write the paper section by section.
        3. Write the paper in a way that is consistent with the scientific products you have.
        4. Do not cite any papers.
        """))
        for tag in SCIENTIFIC_PRODUCT_FIELD_NAMES:
            if tag == 'analysis_codes_and_outputs':
                continue
            prompt = dedent_triple_quote_str("""
            This is the {} part:

            {}

            """).format(tag, getattr(self.scientific_products, tag))
            self.conversation_manager.append_user_message(prompt, tag=f'adding {tag} to pre_paper_conversation')
            self.conversation_manager.append_surrogate_message(content=f'Great! I now know about the {tag}.')

        self.comment("Added all scientific products to the conversation.", tag='after_scientific_products')

    def _write_paper_section(self, section: str):
        prompt = dedent_triple_quote_str("""
            Please write only the `{}` of the paper, do not write any other parts!
            Remember to write the section in tex format including any math or symbols that needs tax escapes.
            """).format(section)
        self.conversation_manager.append_user_message(prompt, tag=f'request_{section}')
        max_attempts = MAX_SECTION_RECREATION_ATTEMPTS
        for attempt in range(max_attempts):
            assistant_response = self.conversation_manager.get_and_append_assistant_message(tag=f'{section}')
            try:
                latex_content = extract_latex_section_from_response(assistant_response, section)
            except FailedToExtractLatexContent as e:
                self.conversation_manager.append_user_message(
                    content=dedent_triple_quote_str("""
                    Your response is not correctly latex formatted. 
                    In particular: {}
                    
                    Please rewrite the {} part again with the correct latex formatting.
                    """).format(e, section),
                    comment=f"The {section} had a latex formatting error (attempt {attempt + 1} / {max_attempts})"
                )
            else:
                # no error was raised, save the content of the section
                # TODO: we should try to format the latex and report formatting errors to chatgpt
                self.comment(f"{section} section of the paper successfully created.")
                setattr(self.paper_sections, section, latex_content)
                return latex_content
        else:
            # we failed to create the section
            self.comment(f"Failed to create the {section} section of the paper after {max_attempts} attempts.")
            return False

    def _write_paper_step_by_step(self):
        """
        write the paper section by section, after each section restart conversation to the abstract.
        """

        # TODO: ultimately, we might want to designate for each section we are writing what are sections to present.
        #  These other presented sections can be presented in full or as summaries.

        # write the abstract
        self._write_paper_section('abstract')
        self.conversation_manager.reset_back_to_tag('ready_for_abstract')
        abstract_prompt = dedent_triple_quote_str("""
        The abstract of the paper is:

        {}

        """).format(self.paper_sections.abstract)
        self.conversation_manager.append_user_message(abstract_prompt, tag='abstract_written')
        # write the rest of the paper
        for section in PAPER_SECTION_FIELD_NAMES:
            if section == 'abstract':
                continue
            self._write_paper_section(section)
            self.conversation_manager.reset_back_to_tag('abstract_written')

    def _assemble_paper(self):
        """
        assemble the paper from the different sections.
        """
        with open(self.paper_template_filename, 'r') as f:
            paper_template = f.read()
        # replace each section with the corresponding section, in the paper template the sections are marked with
        # @@@section_name@@@
        for section in PAPER_SECTION_FIELD_NAMES:
            paper_template = paper_template.replace(f'@@@{section}@@@', getattr(self.scientific_products, section))
        # write the paper to a file
        with open(self.paper_filename, 'w') as f:
            f.write(paper_template)
        # compile the paper
        os.system(f'pdflatex {self.paper_filename}')

    def write_paper(self):
        self.conversation_manager.create_conversation()
        self._populate_conversation()
        self._write_paper_step_by_step()
        self._assemble_paper()
