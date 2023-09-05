"""
WIP approaches for latex parsing
not currently in use
"""

import re
from typing import Tuple, List, Callable, Optional


class TexMathParser:
    def __init__(self):
        self.texmathp_environments = []
        self.texmathp_macros = []
        self.texmathp_onoff_regexp = None
        self.texmathp_toggle_regexp = None
        self.texmathp_tex_commands1 = []

        self.texmathp_command_regexp = re.compile(pattern=r"\\[a-zA-Z]+\*?")
        self.texmathp_switch_regexp = re.compile(pattern=r"\\([" + re.escape("*$_[]") + "])")

        self.texmathp_tex_commands_default = [
            ("$$", "sw-toggle"),
            ("$", "sw-toggle"),
            ("\\hbox", "arg-off"),
            ("\\vbox", "arg-off"),
            ("\\vtop", "arg-off"),
            ("\\vcenter", "arg-off"),
            ("equation", "env-on"),
            ("eqnarray", "env-on"),
            ("eqnarray*", "env-on"),
            ("math", "env-on"),
            ("displaymath", "env-on"),
            ("minipage", "env-off"),
            ("\\fbox", "arg-off"),
            ("\\mbox", "arg-off"),
            ("\\framebox", "arg-off"),
            ("\\label", "arg-off"),
            ("\\textrm", "arg-off"),
            ("\\(", "sw-on"), ("\\)", "sw-off"),
            ("\\[", "sw-on"), ("\\]", "sw-off"),
            ("\\ensuremath", "arg-on"),
            # caption commands
            ("\\caption", "arg-off"),

            # ... Add other commands here ...
        ]

        self.texmathp_tex_commands = []  # Include your custom texmathp_tex_commands here

        self._pattern = None

    def compile(self):
        if self._pattern is not None:
            return

        self.texmathp_environments = []
        self.texmathp_macros = []

        self.texmathp_tex_commands1 = self.texmathp_tex_commands + self.texmathp_tex_commands_default

        switches = []
        togglers = []

        for command, cmd_type in self.texmathp_tex_commands1:
            if cmd_type == "env-on" or cmd_type == "env-off":
                self.texmathp_environments.append(command)
                switches.append("\\begin{" + command + "}")
                switches.append("\\end{" + command + "}")
            elif cmd_type == "arg-on" or cmd_type == "arg-off":
                self.texmathp_macros.append(command)
            elif cmd_type == "sw-on" or cmd_type == "sw-off":
                switches.append(command)
            elif cmd_type == "sw-toggle":
                togglers.append(command)

        self.texmathp_onoff_regexp = r"|".join(map(re.escape, switches))
        self.texmathp_toggle_regexp = r"|".join(map(re.escape, togglers))

        # Match all environments, macros, and switches in latex_str
        self._pattern = re.compile(
            pattern=r"\\begin\{([^}]+)\}|\\end\{([^}]+)\}|"
                    + self.texmathp_onoff_regexp + "|"
                    + self.texmathp_toggle_regexp
        )

    def match_environment(self, latex_str, bound):
        env_match = None
        for match in re.finditer(pattern=r"\\begin\{([^}]+)\}|\\end\{([^}]+)\}", string=latex_str):
            if match.start() < bound:
                continue
            if match.group(1):
                env_match = (match.group(1), match.start())
                break
            elif match.group(2):
                env_match = None
        return env_match

    def match_macro(self, latex_str, bound):
        pos = None
        cmd = None
        syntax_table = str.maketrans({"\\": "\\\\", "[": "\\[", "]": "\\]", "{": "\\{", "}": "\\}"})
        content = latex_str[bound:]
        while "[" in content or "{" in content:
            content = content.translate(syntax_table)
            try:
                content_pos = content.index("[") if "[" in content else len(content)
                brace_pos = content.index("{") if "{" in content else len(content)
                if content_pos < brace_pos:
                    cmd_match = self.texmathp_command_regexp.match(content, content_pos)
                    if cmd_match:
                        cmd = cmd_match.group(0)
                        pos = cmd_match.start(0) + bound
                        break
                    else:
                        content = content[content_pos + 1:]
                else:
                    content = content[brace_pos + 1:]
            except ValueError:
                break
        return cmd, pos

    def match_switch(self, latex_str, bound):
        switch_match = re.search(self.texmathp_switch_regexp, latex_str[bound:])
        if switch_match:
            return switch_match.group(1), switch_match.start(1)
        return None, None

    def parse(self, latex_str, pos):
        self.compile()
        math_on = False

        for match in re.finditer(self._pattern, latex_str):
            start, end = match.span()
            if end <= pos:
                cmd = match.group(0)
                env_begin = match.group(1)
                env_end = match.group(2)

                if env_begin:
                    cmd_type = "env-on" if env_begin in self.texmathp_environments else None
                elif env_end:
                    cmd_type = "env-off" if env_end in self.texmathp_environments else None
                else:
                    cmd_type = next((cmd_type for c, cmd_type in self.texmathp_tex_commands1 if c == cmd), None)

                if cmd_type == "env-on" or cmd_type == "arg-on" or cmd_type == "sw-on":
                    math_on = True
                elif cmd_type == "env-off" or cmd_type == "arg-off" or cmd_type == "sw-off":
                    math_on = False
                elif cmd_type == "sw-toggle":
                    math_on = not math_on
            elif start <= pos and end > pos:
                return None
            elif start > pos:
                break

        # check for backslash
        if pos > 0 and latex_str[pos - 1] == '\\':
            return None

        return math_on

    def separate_latex(self, latex_str):
        self.compile()

        results = []
        current_mode = 'text'
        current_text = ''
        pos = 0

        for match in re.finditer(self._pattern, latex_str):
            start, end = match.span()
            token = match.group(0)

            # Append the text before the token
            if start > pos:
                current_text += latex_str[pos:start]
                if current_text:
                    results.append((current_mode, current_text))
                    current_text = ''

            # Determine the type of the token
            env_begin = match.group(1)
            env_end = match.group(2)

            if env_begin:
                token_type = "env-on" if env_begin in self.texmathp_environments else None
            elif env_end:
                token_type = "env-off" if env_end in self.texmathp_environments else None
            else:
                token_type = next((cmd_type for c, cmd_type in self.texmathp_tex_commands1 if c == token), None)

            # Change mode based on the token type
            if token_type in ['env-on', 'arg-on', 'sw-on']:
                if current_mode == 'text':
                    current_mode = 'math'
                results.append(('tag', token))
            elif token_type in ['env-off', 'arg-off', 'sw-off']:
                if current_mode == 'math':
                    current_mode = 'text'
                results.append(('tag', token))
            elif token_type == 'sw-toggle':
                results.append(('text', current_text))
                results.append(('tag', token))
                current_text = ''
                current_mode = 'math' if current_mode == 'text' else 'text'

            pos = end

        # Append the text after the last token
        if pos < len(latex_str):
            current_text += latex_str[pos:]

        if current_text:
            results.append((current_mode, current_text))

        # Remove empty text fragments
        results = [(mode, text) for mode, text in results if text]

        return results


# more safe - but slow:
def separate_latex_safe(latex: str) -> List[Tuple[str, str]]:
    """
    Separate a latex document into a list of (type, string) tuples, where type is either 'text', 'math', 'tag'.
    """

    results = []
    parser = TexMathParser()

    result_to_type = {
        None: 'tag',
        True: 'math',
        False: 'text',
    }
    current_text = ''
    current_type_ = ''
    for pos in range(len(latex)):
        result = parser.parse(latex, pos)
        type_ = result_to_type[result]
        if type_ != current_type_:
            if current_text:
                results.append((current_type_, current_text))
            current_type_ = type_
            current_text = ''
        current_text += latex[pos]
    results.append((current_type_, current_text))
    return results


def separate_latex(latex: str) -> List[Tuple[str, str]]:
    """
    Separate a latex document into a list of (type, string) tuples, where type is either 'text', 'math', 'tag'.
    """
    parser = TexMathParser()
    results = parser.separate_latex(latex)
    return results


def process_latex(latex: str, process_math: Optional[Callable] = None, process_text: Optional[Callable] = None) -> str:
    """
    Process a latex document, where `process_math` is a function that receives a math string and returns a string, and
    `process_text` is a function that receives a text string and returns a string.
    """

    funcs = {
        'math': process_math or (lambda x: x),
        'text': process_text or (lambda x: x),
        'tag': lambda x: x,
    }

    results = separate_latex_safe(latex)
    processed = [funcs[type_](text) for type_, text in results]
    return ''.join(processed)


# ANOTHER APPROACH, with "pylatexenc":

from pylatexenc.latexwalker import LatexWalker, LatexCharsNode, LatexGroupNode

latex_str = r"\textbf{Bold} and \emph{emphasized} text."

# Save the original latex_verbatim methods
original_latex_verbatim_chars = LatexCharsNode.latex_verbatim
original_latex_verbatim_group = LatexGroupNode.latex_verbatim

# Monkeypatch the latex_verbatim method to use the chars attribute for CharsNode
def new_latex_verbatim_chars(self):
    return self.chars.upper()

# Monkeypatch the latex_verbatim method for GroupNode
def new_latex_verbatim_group(self):
    return '{' + ''.join(n.latex_verbatim() for n in self.nodelist) + '}'

LatexCharsNode.latex_verbatim = new_latex_verbatim_chars
LatexGroupNode.latex_verbatim = new_latex_verbatim_group

# Initialize a walker
walker = LatexWalker(latex_str)
nodes, _, _ = walker.get_latex_nodes(pos=0)

# Convert nodes back to LaTeX
modified_latex = ''.join(n.latex_verbatim() for n in nodes if n is not None)
print(modified_latex)

# Restore the original latex_verbatim methods
LatexCharsNode.latex_verbatim = original_latex_verbatim_chars
LatexGroupNode.latex_verbatim = original_latex_verbatim_group
