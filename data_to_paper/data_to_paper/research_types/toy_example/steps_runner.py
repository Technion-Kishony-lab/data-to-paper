from dataclasses import dataclass, field
from typing import Type

from data_to_paper.base_steps.base_steps_runner import DataStepRunner
from data_to_paper.conversation.stage import Stage

from .app_startup import ToyStartDialog
from .cast import DemoAgent
from .coding_steps import DemoCodeProductsGPT
from .produce_pdf_step import ProduceDemoPaperPDF
from .products import DemoProducts
from .stage import DemoStages
from .writing_steps import WriteTitleAndAbstract


@dataclass
class ToyStepsRunner(DataStepRunner):
    PROJECT_PARAMETERS_FILENAME = 'data_to_paper-toy-example.json'
    DEFAULT_PROJECT_PARAMETERS = DataStepRunner.DEFAULT_PROJECT_PARAMETERS | dict(
        research_goal=None
    )
    APP_STARTUP_CLS = ToyStartDialog
    name = 'Toy Example Research'
    stages: Type[Stage] = DemoStages
    cast = DemoAgent
    products: DemoProducts = field(default_factory=DemoProducts)

    def _run_all_steps(self) -> DemoProducts:

        products = self.products  # Start with empty products
        products.data_file_descriptions = self.data_file_descriptions
        products.research_goal = self.project_parameters['research_goal']

        # Get the paper section names:
        paper_producer = ProduceDemoPaperPDF.from_(
            self,
            output_filename='paper.pdf',
            paper_section_names=['title', 'abstract'],
        )

        self.advance_stage(DemoStages.DATA)
        self.send_product_to_client('data_file_descriptions')

        # Goal
        self.advance_stage(DemoStages.GOAL)
        self.send_product_to_client('research_goal')

        # Write code
        self.advance_stage(DemoStages.CODE)
        products.code_and_output = DemoCodeProductsGPT.from_(self).get_code_and_output()
        self.send_product_to_client('code_and_output')

        # Title and abstract
        self.advance_stage(DemoStages.WRITING)
        section_names = ['title', 'abstract']
        sections = WriteTitleAndAbstract.from_(self, section_names=section_names).run_and_get_valid_result()
        for section_name, section in zip(section_names, sections):
            products.paper_sections[section_name] = section
        self.send_product_to_client('title_and_abstract')

        # Compile the paper
        self.advance_stage(DemoStages.COMPILE)
        paper_producer.assemble_compile_paper()
        self._app_clear_panels()
        self._app_send_product_of_stage(
            DemoStages.COMPILE,
            f'<a href="file://{self.output_directory}/paper.pdf">Download the manuscript</a>')
        self.advance_stage(True)

        return products
