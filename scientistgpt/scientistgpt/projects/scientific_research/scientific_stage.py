from scientistgpt.conversation.stage import Stage


class ScientificStage(Stage):
    PLANNING = "planning"
    CODING = "coding"
    ANALYSIS = "analysis"
    WRITING = "writing"
    FINISHED = "finished"
    FAILED = "failed"
