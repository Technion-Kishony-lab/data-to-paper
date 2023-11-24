# This module is meant to be imported by chatgpt.

import inspect
import re
import sys
from typing import Tuple
# You can add more imports as needed. If they are not available, we will install them for you.


# You can add new functions here and call them from the `respond_to_chatgpt_and_alter_self_code` function.


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
    (6) Repeat from step (1)

    You should make any changes to this function or the entire module as you see fit and helpful.
    To make changes to this function (or anything else in the module), you should simply include in your message
    a Dict[str, str] mapping from old code to new code.
    """

    current_module = sys.modules[__name__]
    module_code = inspect.getsource(current_module)

    new_module_code = module_code

    extracted_dict_match = re.search(pattern=r'\{.*\}', string=chatgpt_message, flags=re.DOTALL)
    if not extracted_dict_match:
        return "Unable to find a Dict[str, str] mapping in your message.\n" \
               "To update my code, please respond with a code mapping as a Dict[str, str].", module_code
    try:
        old_code_to_new_code = eval(extracted_dict_match.group(0))
        for old_code, new_code in old_code_to_new_code.items():
            if old_code not in module_code:
                return f"I was unable to find '{old_code}' in my code.\n", module_code
            new_module_code = new_module_code.replace(old_code, new_code)
    except Exception as e:
        return f"Unable to evaluate the code mapping in your message. Error: \n{e}", module_code

    if new_module_code == module_code:
        return "My code did not change :(\n" \
               "Please send me a message that includes a valid code mapping.", module_code

    response = "Yeh! I have successfully updated my code based on your message :)\n" \
               "On your next message, this new code will run and respond accordingly.\n" \
               "Keep sending me messages to improve me further!"

    return response, new_module_code
