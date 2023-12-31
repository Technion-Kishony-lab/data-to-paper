from data_to_paper.research_types.scientific_research.coding_steps import CreateTableDataframesCodeProductsGPT
from data_to_paper.run_gpt_code.dynamic_code import RunCode

module = 'data_to_paper_examples.examples.projects.congress_twitter.outputs.open_goal_accum_3.ttt'

RunCode(additional_contexts={},  # CreateTableDataframesCodeProductsGPT().additional_contexts,
        run_folder='inputs/temp_folder',
        allowed_open_read_files=None,
        allowed_open_write_files=None,
        output_file_requirements=None,
        ).run(module_filepath=module)
