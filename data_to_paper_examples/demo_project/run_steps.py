from dataclasses import dataclass, field
from typing import Optional

from data_to_paper.base_steps.base_steps_runner import BaseStepsRunner
from data_to_paper.base_steps.request_products_from_user import DirectorProductGPT
from cast import DemoAgent
from coding_steps import DemoCodeProductsGPT
from produce_pdf_step import ProduceDemoPaperPDF
from products import DemoProducts
from stage import DemoStages
from writing_steps import WriteTitleAndAbstract


@dataclass
class DemoStepsRunner(BaseStepsRunner):

    cast = DemoAgent
    products: DemoProducts = field(default_factory=DemoProducts)
    research_goal: Optional[str] = None

    def _run_all_steps(self) -> DemoProducts:

        products = self.products  # Start with empty products

        # Get the paper section names:
        paper_producer = ProduceDemoPaperPDF.from_(
            self,
            output_filename='paper.pdf',
            paper_section_names=[]
        )

        # Data file descriptions:
        director_converser = DirectorProductGPT.from_(self,
                                                      assistant_agent=DemoAgent.Director,
                                                      user_agent=DemoAgent.Performer,
                                                      conversation_name='with_director',
                                                      )
        self.advance_stage_and_set_active_conversation(DemoStages.DATA, DemoAgent.Director)
        products.data_file_descriptions = director_converser.get_product_or_no_product_from_director(
            product_field='data_file_descriptions', returned_product=self.data_file_descriptions)
        self.send_product_to_client('data_file_descriptions')

        # Goal
        self.advance_stage_and_set_active_conversation(DemoStages.DATA, DemoAgent.Director)
        products.research_goal = director_converser.get_product_or_no_product_from_director(
            product_field='research_goal', returned_product=self.research_goal,
            acknowledge_no_product_message="OK. no problem. I will devise the goal myself.")

        # Write code
        self.advance_stage_and_set_active_conversation(
            DemoStages.CODE, DemoAgent.Debugger)
        products.code_and_output = DemoCodeProductsGPT.from_(self).get_code_and_output()
        self.send_product_to_client('code_and_output')

        # Paper sections
        section_names = ['title', 'abstract']
        sections = WriteTitleAndAbstract.from_(self, section_names=section_names).run_dialog_and_get_valid_result()
        for section_name, section in zip(section_names, sections):
            products.paper_sections[section_name] = section
        self.send_product_to_client('paper_sections')

        paper_producer.assemble_compile_paper()

        return products
