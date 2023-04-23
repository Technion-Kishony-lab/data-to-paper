from dataclasses import dataclass, field
from typing import Optional, List

from scientistgpt.gpt_interactors.scientific_products import ScientificProducts, SCIENTIFIC_PRODUCT_FIELD_NAMES
from scientistgpt.latex import extract_latex_section_from_response, FailedToExtractLatexContent
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.text_utils import concat_words_with_commas_and_and

from .base_paper_writing import PaperWritingGPT, FailedCreatingPaperSection

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
            self.apply_append_user_message(prompt, tag=tag)
            self.apply_append_surrogate_message(
                content=f"Thank you for providing the {tag.replace('_', ' ')}.")

        self.comment("All scientific products have been added to the conversation.", tag='after_scientific_products')

    def _write_specified_paper_sections(self, section_names: List[str], prompt: str = None):
        """
        Write the specific section(s) of the paper.
        """
        prompt = prompt or dedent_triple_quote_str("""
            Please write only the `{}` of the paper. Do not write any other parts!
            Remember to write in tex format including any math or symbols that needs tex escapes.
            """).format(concat_words_with_commas_and_and(section_names))
        self.apply_append_user_message(prompt)
        max_attempts = MAX_SECTION_RECREATION_ATTEMPTS
        for attempt in range(max_attempts):
            assistant_response = self.apply_get_and_append_assistant_message(tag=f'{section_names}')
            try:
                for section_name in section_names:
                    self.paper_sections[section_name] = \
                        extract_latex_section_from_response(assistant_response, section_name)
            except FailedToExtractLatexContent as e:
                self.apply_append_user_message(
                    content=dedent_triple_quote_str("""
                        {}

                        Please rewrite the {} part again with the correct latex formatting.
                        """).format(e, concat_words_with_commas_and_and(section_names)),
                    comment=f"Latex formatting error (attempt {attempt + 1} / {max_attempts})")
            else:
                # we successfully created all the sections
                self.comment(f'Section "{section_names}" successfully created.')
                return
        # we failed to create the sections after max attempts
        raise FailedCreatingPaperSection(section_names[0])

    def _get_paper_sections(self):
        """
        Fill all the paper sections in paper_sections
        """

        # We start with the title and abstract:
        self._write_specified_paper_sections(['title', 'abstract'])
        self.conversation_manager.reset_back_to_tag('after_scientific_products')
        abstract_prompt = dedent_triple_quote_str("""
        Here are the title and abstract of the paper:

        {}

        {}
        """).format(self.paper_sections['title'], self.paper_sections['abstract'])
        self.apply_append_user_message(abstract_prompt, tag='title_and_abstract')

        # We then write each of the other sections in light of the title and abstract:
        for section_name in self.paper_section_names:
            if section_name in self.paper_sections:
                continue
            self._write_specified_paper_sections([section_name])
            self.conversation_manager.reset_back_to_tag('title_and_abstract')
