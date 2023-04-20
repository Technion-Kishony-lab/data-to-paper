import requests


def latex_to_pdf(latex_content: str, filename: str):
    """
    Convert a LaTeX file to PDF using latexonline.cc server and save the PDF as a local file.
    """
    assert filename.endswith('.pdf'), 'The filename should end with .pdf'

    url = 'https://latexonline.cc/compile'
    data = {
        'text': latex_content,
        'compiler': 'pdflatex'
    }

    response = requests.post(url, data=data)

    with open(filename, 'wb') as f:
        f.write(response.content)
