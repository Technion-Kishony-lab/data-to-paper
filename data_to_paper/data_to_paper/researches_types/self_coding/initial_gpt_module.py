# This module is meant to be imported by chatgpt.

import inspect
import re
import sys
from typing import Tuple
# <Add additional imports here>


# Functions:

def do_something(chatgpt_message: str) -> str:
    return "I am doing something!"

# <Add additional functions here>



def respond_to_chatgpt_and_alter_self_code(chatgpt_message: str) -> Tuple[str, str]:
    """
    Self-altering function that responds to chatgpt and alters its own code.

    The function is called within a perfectly safe and isolated environment,
    by a platform that takes care of the following steps:
    (1) Request a response from chatgpt
    (2) Import the module that contains this function
    (3) Call this function with the message from chatgpt (passed as the `chatgpt_message` argument) and
        getting back a `response` and a `new_module_code`.
    (4) Updating the code of the module with the `new_module_code`.
    (5) Sending the `response` and the `new_module_code` back to chatgpt.
    (6) Go back to (1)

    You can make any changes to this function or the entire module as you see fit and helpful.

    To make changes to this function (or anything else in the module), you should simply include in your message
    a Dict[str, str] mapping of old code strings to new code string. Your Dict[str, str] should be enclosed in triple
    backticks.

    You can design changes to the code to either:

    * Enhance the self-altering functionality.
    For example, to make sure only the first occurrence of the old code is replaced with the new code,
    you can send a message containing:
    ```
    {
        'replace(old_code, new_code)':
            'old_code = old_code.replace(old_code, new_code, 1)'
    }
    ```

    * You can make the code do something new.
    For example, if you want to create a function that adds two numbers, you can send the following message:
    ```
    {
        'return "I am doing something!"':
            'split = chatgpt_message.split()\n'
            'a = int(split[0])\n'
            'b = int(split[1])\n'
            'return "The sum of {a} and {b} is {a + b}"\n'
    }
    ```


    Think creatively about what you can do with this platform.

    """

    current_module = sys.modules[__name__]
    module_code = inspect.getsource(current_module)

    new_module_code = module_code

    extracted_dict_match = re.search(pattern=r"```(.*?)```", string=chatgpt_message, flags=re.DOTALL)
    if not extracted_dict_match:
        raise Exception("Unable to find a Dict[str, str] mapping in the LLM-ASSISTANT message")

    old_code_to_new_code = eval(extracted_dict_match.group(0))

    for old_code, new_code in old_code_to_new_code.items():
        if old_code not in module_code:
            raise Exception(f"Unable to find '{old_code}' in existing code.")
        new_module_code = new_module_code.replace(old_code, new_code)

    if new_module_code == module_code:
        return "My code did not change :(\n" \
               "Please send me a message that includes a valid code mapping.", module_code

    response = do_something(chatgpt_message)

    if new_module_code != module_code:
        response += """\n
            Yeh! I have successfully updated my code based on your message :)
            On your next message, this new code will run and respond accordingly.
            Keep sending me messages to improve me further!
            """

    return response, new_module_code
