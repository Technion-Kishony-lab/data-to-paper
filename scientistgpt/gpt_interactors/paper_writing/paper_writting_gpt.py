from dataclasses import dataclass, field
from typing import Optional

from scientistgpt.gpt_interactors.scientific_products import ScientificProducts, SCIENTIFIC_PRODUCT_FIELD_NAMES
from scientistgpt.latex import extract_latex_section_from_response, FailedToExtractLatexContent
from scientistgpt.utils import dedent_triple_quote_str
from .base_paper_writing import PaperWritingGPT

MAX_SECTION_RECREATION_ATTEMPTS = 3


@dataclass
class PaperAuthorGPT(PaperWritingGPT):
    """
    Interact with chatgpt to write a scientific paper.

    the context we need for the paper writing process is the `scientific_products`, including:
    data description, goal description, analysis plan, analysis results description, implications of results,
    and limitations of results.

    the paper writing process is:
    - write an abstract
    - add abstract to the conversation
    - based on the abstract, write all other sections (title, introduction, methods, results, discussions, conclusions)
    - create figures supporting the results (TBD)
    - assemble the sections into a paper
    """

    conversation_name: str = 'pre_paper_conversation'

    scientific_products: Optional[ScientificProducts] = field(default_factory=ScientificProducts)

    def _pre_populate_conversation(self):
        for tag in SCIENTIFIC_PRODUCT_FIELD_NAMES:
            if tag == 'analysis_codes_and_outputs':
                continue
            prompt = dedent_triple_quote_str("""
            This is the "{}" part:

            {}

            """).format(tag.replace('_', ' '), getattr(self.scientific_products, tag))
            self.conversation_manager.append_user_message(prompt, tag=tag)
            self.conversation_manager.append_surrogate_message(
                content=f"Thank you for providing the {tag.replace('_', ' ')}.")

        self.comment("All scientific products have been added to the conversation.", tag='after_scientific_products')

    def _write_paper_section(self, section_name: str) -> str:
        """
        Write a specific section of the paper.
        """
        prompt = dedent_triple_quote_str("""
            Please write only the `{}` of the paper. Do not write any other parts!
            Remember to write the section in tex format including any math or symbols that needs tax escapes.
            """).format(section_name)
        self.conversation_manager.append_user_message(prompt, tag=f'request_{section_name}')
        max_attempts = MAX_SECTION_RECREATION_ATTEMPTS
        for attempt in range(max_attempts):
            assistant_response = self.conversation_manager.get_and_append_assistant_message(tag=f'{section_name}')
            try:
                latex_content = extract_latex_section_from_response(assistant_response, section_name)
            except FailedToExtractLatexContent as e:
                self.conversation_manager.append_user_message(
                    content=dedent_triple_quote_str("""
                    Your response is not correctly latex formatted. 
                    In particular: {}

                    Please rewrite the {} part again with the correct latex formatting.
                    """).format(e, section_name),
                    comment=f"Latex formatting error detected (attempt {attempt + 1} / {max_attempts})"
                )
            else:
                # no error was raised, save the content of the section
                self.comment(f'Section "{section_name}" successfully created.')
                self.paper_sections[section_name] = latex_content
                return latex_content
        else:
            # we failed to create the section
            assert False, f"Failed to create the {section_name} section of the paper after {max_attempts} attempts."

    def _get_paper_sections(self):
        """
        Fill all the paper sections in paper_sections
        """

        # TODO: ultimately, we might want to designate for each section we are writing what are sections to present.
        #  These other presented sections can be presented in full or as summaries.

        # write the abstract
        self._write_paper_section('abstract')
        self.conversation_manager.reset_back_to_tag('after_scientific_products')
        abstract_prompt = dedent_triple_quote_str("""
        The abstract of the paper is:

        {}

        """).format(self.paper_sections['abstract'])
        self.conversation_manager.append_user_message(abstract_prompt, tag='abstract_written')

        # write the rest of the paper
        for section_name in self.paper_section_names:
            if section_name in self.paper_sections:
                continue
            self._write_paper_section(section_name)
            self.conversation_manager.reset_back_to_tag('abstract_written')
