def prepare_pre_paper_conversation(self):
    print_red('Preparing the pre-paper conversation ...', message_callback=self.message_callback)
    paper_conversation = Conversation()
    paper_conversation.append_message(role=Role.SYSTEM,
                                      message='You are a helpful scientist that able to write scientific papers.')
    paper_conversation.append_user_message('This is the data description\n\n' + self.data_description)
    paper_conversation.append_assistant_message('acknowledged')
    paper_conversation.append_user_message('This is the research goal description\n\n' + self.goal_description)
    paper_conversation.append_assistant_message('acknowledged')
    paper_conversation.append_user_message('This is the analysis plan description\n\n' + self.analysis_plan)
    paper_conversation.append_assistant_message('acknowledged')
    paper_conversation.append_user_message('This is the analysis results description\n\n' + self.results_summary)
    paper_conversation.append_assistant_message('acknowledged')
    print_red('Pre-paper conversation is ready! Let\'s write the paper ...', message_callback=self.message_callback)
    self.pre_paper_conversation = paper_conversation


def write_paper(self):
    prompt = dedent_triple_quote_str("""
    Write paper - write abstract, introduction, methods, results, discussion and acknowledgments.
    Use markdown to format the paper.
    In addition you are required to state where to enter the figure of you created during the analysis by using
    FIGURE@#@ name_of_figure @#@ where name_of_figure is the name of the figure you want to enter.
    Add references to the paper if applicable.
    """)
    self.pre_paper_conversation.append_user_message(prompt)
    self.pre_paper_conversation.get_response_from_chatgpt()
    paper = self.pre_paper_conversation.get_last_response()
    self.conversation.append_user_message(prompt)
    self.conversation.append_assistant_message(paper)
    # save the paper to file
    with open('paper.txt', 'w') as f:
        f.write(paper)
