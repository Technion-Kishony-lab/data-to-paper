from dataclasses import dataclass, field
from typing import Optional

from g3pt.base_steps.base_runner import BaseStepsRunner
from g3pt.base_steps.director_converser import DirectorProductGPT

from .cast import ScientificAgent
from .add_citations import AddCitationReviewGPT
from .get_template import get_paper_template_path
from .scientific_products import ScientificProducts
from .steps import GoalReviewGPT, PlanReviewGPT, \
    ResultsInterpretationReviewGPT, PaperSectionReviewGPT, TitleAbstractReviewGPT, PaperSectionWithTablesReviewGPT, \
    ScientificCodeProductsGPT, ProduceScientificPaperPDF, ProduceScientificPaperPDFWithAppendix

PAPER_TEMPLATE_FILE: str = get_paper_template_path('standard_paper.tex')
SECTIONS_TO_ADD_CITATIONS_TO = ['introduction', 'discussion']
SECTIONS_TO_ADD_TABLES_TO = ['results']


@dataclass
class ScientificStepsRunner(BaseStepsRunner):

    products: ScientificProducts = field(default_factory=ScientificProducts)
    research_goal: Optional[str] = None

    def _run_all_steps(self) -> ScientificProducts:
        products = self.products
        paper_producer = ProduceScientificPaperPDFWithAppendix(
            paper_template_filepath=PAPER_TEMPLATE_FILE,
            products=products,
            output_file_path=self.output_directory / 'paper.pdf',
        )
        paper_section_names = paper_producer.get_paper_section_names()

        # Data file descriptions:
        director_converser = DirectorProductGPT(
            products=products,
            assistant_agent=ScientificAgent.Director,
            user_agent=ScientificAgent.Student,
            conversation_name='with_director',
        )
        products.data_file_descriptions = director_converser.get_product_from_director(
            product_field='data_file_descriptions', returned_product=self.data_file_descriptions)

        # Goal
        if self.research_goal is None:
            products.research_goal = GoalReviewGPT(products=products).initialize_and_run_dialog()
        else:
            products.research_goal = director_converser.get_product_from_director(
                product_field='research_goal', returned_product=self.research_goal)

        # Analysis plan
        products.analysis_plan = PlanReviewGPT(products=products).initialize_and_run_dialog()

        # Code and output
        products.code_and_output = ScientificCodeProductsGPT(products=products).get_analysis_code()

        # Results interpretation
        products.results_summary = ResultsInterpretationReviewGPT(products=products).initialize_and_run_dialog()

        # Paper sections
        title_and_abstract_names = ['title', 'abstract']
        products.paper_sections['title'], products.paper_sections['abstract'] = \
            TitleAbstractReviewGPT(products=products, section_names=title_and_abstract_names).get_sections()

        for section_name in paper_section_names:
            if section_name not in title_and_abstract_names:
                products.paper_sections[section_name] = \
                    PaperSectionReviewGPT(products=products, section_name=section_name).get_section()

        # Add citations to relevant paper sections
        for section_name in SECTIONS_TO_ADD_CITATIONS_TO:
            products.cited_paper_sections[section_name] = \
                AddCitationReviewGPT(products=products, section_name=section_name).rewrite_section_with_citations()

        # Add tables to results section
        for section_name in SECTIONS_TO_ADD_TABLES_TO:
            products.paper_sections_with_tables[section_name] = \
                PaperSectionWithTablesReviewGPT(products=products, section_name=section_name).get_section()

        paper_producer.assemble_compile_paper()

        return products
