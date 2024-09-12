from data_to_paper.llm_coding_utils import df_to_figure


def test_plot_with_caption_and_label(test_data):
    latex = df_to_figure(test_data, filename='test', caption='Test Caption', y='y')
    assert "df.plot(y='y')" in latex
    assert "Test Caption" in latex


def test_plot_with_note_and_glossary(test_data):
    note = 'This is a note.'
    glossary = {'y': 'Y-axis values'}
    latex = df_to_figure(test_data, filename='test', note=note, glossary=glossary, y='y')
    assert "df.plot(y='y')" in latex
    assert "y: Y-axis values" in latex


def test_plot_with_all_options(test_data):
    latex = df_to_figure(test_data, filename='test', caption='Full options', note='Note here',
                         glossary={'x': 'X values', 'y': 'Y values'}, xlabel='X Axis', ylabel='Y Axis', y='y',
                         yerr='y_err', y_p_value='y_p_value')
    assert "df.plot(xlabel='X Axis', ylabel='Y Axis', y='y', yerr='y_err')" in latex
    assert '*** p $<$ 0.0001' in latex
    assert r'\caption{Full options' in latex
    assert 'Note here' in latex


# PDF_FOLDER = Path(__file__).parent / 'pdfs'
#
#
# def test_df_to_figure_compilation(test_data):
#     latex = df_to_figure(test_data, filename='test', caption='Test Caption', y='y',
#                          create_fig=True, figure_folder=PDF_FOLDER)
#     # compile the latex to pdf:
#     with run_in_directory(PDF_FOLDER):
#         LatexDocument().get_document(latex, output_directory=PDF_FOLDER, file_stem='test',
#                                      figures_folder=PDF_FOLDER)
#
