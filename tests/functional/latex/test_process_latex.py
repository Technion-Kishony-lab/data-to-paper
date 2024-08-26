import pytest

from data_to_paper.latex.clean_latex import process_latex_text_and_math


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "$This is Math$ This is Text $This is Math$",
            "$THIS IS MATH$ this is text $THIS IS MATH$",
        ),
        (
            "This is Text $This is Math$",
            "this is text $THIS IS MATH$",
        ),
        (
            "$This is Math$ This is Text",
            "$THIS IS MATH$ this is text",
        ),
        (
            "This is Text \\(This is Math\\) This is Text",
            "this is text \\(THIS IS MATH\\) this is text",
        ),
        (
            "\\begin{tabular}\\This is a Table\\end{tabular}",
            "\\begin{tabular}\\this is a table\\end{tabular}",
        ),
        (
            "\\begin{tabular}\\caption{This is a Caption}\\end{tabular}",
            "\\begin{tabular}\\caption{this is a caption}\\end{tabular}",
        ),
        (
            "Text Before \\begin{tabular}\\caption{This is a Caption}\\end{tabular} Text After",
            "text before \\begin{tabular}\\caption{this is a caption}\\end{tabular} text after",
        ),
        (
            "$Math Before$ \\begin{tabular}\\caption{This is a Caption}\\end{tabular} $Math After$",
            "$MATH BEFORE$ \\begin{tabular}\\caption{this is a caption}\\end{tabular} $MATH AFTER$",
        ),
        (
            "\\begin{figure}\n\\caption{Aaa\nBbb}\n\\end{figure}",
            "\\BEGIN{FIGURE}\n\\caption{aaa\nbbb}\n\\END{FIGURE}",
        )
    ],
)
def test_process_latex_parts(text, expected):
    result = process_latex_text_and_math(text, str.lower, str.upper)
    assert result == expected
