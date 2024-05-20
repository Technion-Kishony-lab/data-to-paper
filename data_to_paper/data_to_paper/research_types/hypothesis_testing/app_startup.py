from data_to_paper.interactive.base_app_startup import DataFilesStartDialog, TextEditWithHeader, MultiFileWidget


class HypothesisTestingStartDialog(DataFilesStartDialog):
    def _create_widgets(self):
        return {
            'general_description': TextEditWithHeader(
                "Dataset description", "Describe the dataset, its origin, content, purpose, etc."),
            'files_widget': MultiFileWidget(),
            'research_goal': TextEditWithHeader(
                "Research Goal", "Specify the research goal, or leave blank for autonomous goal setting."),
        }

    def _convert_config_to_widgets(self, config):
        self.widgets['general_description'].setPlainText(config.get('general_description', ''))
        self.widgets['research_goal'].setPlainText(config.get('research_goal', '') or '')
        super()._convert_config_to_widgets(config)

    def _convert_widgets_to_config(self) -> dict:
        config = self.current_config
        config['general_description'] = self.widgets['general_description'].toPlainText() or None
        config['research_goal'] = self.widgets['research_goal'].toPlainText() or None
        config = super()._convert_widgets_to_config()
        return config
