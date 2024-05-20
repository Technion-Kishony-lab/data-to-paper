from data_to_paper.interactive.base_app_startup import DataFilesStartDialog, TextEditWithHeader, MultiFileWidget, \
    SingleFileWidget


class ToyStartDialog(DataFilesStartDialog):
    def _set_style(self):
        super()._set_style()
        self.resize(600, 500)

    def _create_widgets(self):
        return {
            'research_goal': TextEditWithHeader(
                "Research Goal", "Specify a funny research goal."),
            'files_widget': SingleFileWidget(),
        }

    def _convert_config_to_widgets(self, config):
        self.widgets['research_goal'].setPlainText(config.get('research_goal', '') or '')
        super()._convert_config_to_widgets(config)

    def _convert_widgets_to_config(self) -> dict:
        config = self.current_config
        config['general_description'] = ''
        config['research_goal'] = self.widgets['research_goal'].toPlainText() or None
        config = super()._convert_widgets_to_config()
        return config