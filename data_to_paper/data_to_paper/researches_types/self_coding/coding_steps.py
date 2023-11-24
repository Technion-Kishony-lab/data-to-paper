import builtins
import inspect
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Optional, Tuple, Type, Iterable, Any

from data_to_paper.base_steps import BaseCodeProductsGPT, DebuggerConverser
from cast import DemoAgent
from data_to_paper.researches_types.self_coding import initial_gpt_module
from data_to_paper.run_gpt_code.code_runner import BaseCodeRunner, CodeRunner
from data_to_paper.run_gpt_code.dynamic_code import RunCode
from data_to_paper.run_gpt_code.types import OutputFileRequirement, CodeAndOutput
from data_to_paper.servers.openai_models import ModelEngine
from products import CodingProducts

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList


SELF_FUNC_NAME = 'respond_to_chatgpt_and_alter_self_code'


@dataclass
class SelfRunCode(RunCode):
    chatgpt_response: str = None
    forbidden_imports: Optional[Iterable[str]] = ('os', 'subprocess', 'shutil', 'pickle', 'matplotlib')
    forbidden_modules_and_functions: Iterable[Tuple[Any, str, bool]] = (
        # Module, function, create RunIssue (True) or raise exception (False)
        (builtins, 'print', True),
        (builtins, 'input', False),
        (builtins, 'exit', False),
        (builtins, 'quit', False),
        # (builtins, 'exec', False),
    )

    def _run_function_in_module(self, module: ModuleType):
        """
        Run all functions in the module, except for the self function.
        """
        self_func = getattr(module, SELF_FUNC_NAME, None)
        if self_func is not None and inspect.isfunction(self_func):
            return self_func(self.chatgpt_response)
        else:
            raise ValueError(f'Could not find function {SELF_FUNC_NAME}.')


@dataclass
class SelfCodeRunner(BaseCodeRunner):
    run_code_cls: Type[RunCode] = SelfRunCode
    previous_code: str = None

    def get_raw_code(self) -> str:
        return self.previous_code

    def get_run_code(self) -> RunCode:
        run_code = super().get_run_code()
        run_code.chatgpt_response = self.response
        return run_code


@dataclass
class SelfDebuggerConverser(DebuggerConverser):
    code_runner_cls: Type[BaseCodeRunner] = SelfCodeRunner
    previous_code: str = None

    def _get_code_runner(self, response: str) -> BaseCodeRunner:
        code_runner = super()._get_code_runner(response)
        code_runner.previous_code = self.previous_code
        return code_runner

    def run_debugging(self) -> Optional[CodeAndOutput]:
        self.initialize_conversation_if_needed()
        for self.debug_iteration in range(1, self.max_debug_iterations + 1):
            code_and_output = self._get_code_and_respond_to_issues()
            if code_and_output is not None:
                response, new_code = code_and_output.result
                is_new_code = new_code != self.previous_code
                self.previous_code = new_code
                msg = dedent_triple_quote_str("""
                    Here is the `response` output from the function:
                    ```output
                    {response}
                    ```
                    """).format(response=response)
                if is_new_code:
                    msg += dedent_triple_quote_str("""
                        Here is the new code (the `new_module_code` variable): 
                        ```python
                        {new_code}
                        ```
                        """).format(new_code=new_code)
                self.apply_append_user_message(msg)

        return code_and_output


@dataclass
class SelfCodeProductsGPT(BaseCodeProductsGPT):
    model_engine: ModelEngine = ModelEngine.GPT4
    products: CodingProducts = None
    assistant_agent: DemoAgent = DemoAgent.Performer
    user_agent: DemoAgent = DemoAgent.Debugger
    background_product_fields: Tuple[str, ...] = ()
    gpt_script_filename: str = None
    code_name: str = 'GPT Code'
    debugger_cls: Type[DebuggerConverser] = SelfDebuggerConverser
    attrs_to_send_to_debugger: Tuple[str, ...] = \
        ('output_file_requirements', 'data_filenames', 'data_folder', 'allow_dataframes_to_change_existing_series',
         'enforce_saving_altered_dataframes', 'supported_packages', 'model_engine', )

    output_file_requirements: Tuple[OutputFileRequirement, ...] = ()
    allowed_created_files: Tuple[str, ...] = ()
    allow_dataframes_to_change_existing_series = False
    enforce_saving_altered_dataframes: bool = False

    supported_packages: Tuple[str, ...] = ()

    @property
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.products.data_file_descriptions.get_data_filenames(),
                        wrap_with='"',
                        prefix='{} data file[s]: ')

    @property
    def data_folder(self) -> Optional[Path]:
        return Path(self.products.data_file_descriptions.data_folder)

    def _get_initial_code_and_output(self) -> CodeAndOutput:
        return CodeAndOutput(code=self.initial_code)

    system_prompt: str = dedent_triple_quote_str("""
        You are an adventures programmer who is given a platform to write code and try it out. 
        
        You are given a function that gets a message from chatgpt and based on that response, it does two things:
        (1) Alters the function's own code, or even the code of the module that the function is in.
        (2) Crafts a response to send back to chatgpt
    
        In the next iteration, the module code will get updated and the updated code will run on a new chatgpt message \
        and return a new response.
        
        The process though allows you to write and improve code iteratively.

        Try to think of something creative to do with this platform.

        The function runs in a safe and isolated context, so you don't need to worry about it breaking or \
        doing anything bad.
        """)

    user_initiation_prompt: str = dedent_triple_quote_str("""
        You are chatting with an automated platform that allows you to write and try out code iteratively.
        The first version of the code is:
        
        ```python
        {initial_code}
        ```
        
        The platform will run this code with your response as the `chatgpt_message` input argument and then send \
        you back the output variables: `new_code` and `response`.
        The code will then be updated to the new code and the new code will be run with your next response.
        This way, you can gradually build up the code in any way you want. 
        Try to think of an interesting goal and work step by step towards it.
        """)

    initial_code: str = inspect.getsource(initial_gpt_module)
