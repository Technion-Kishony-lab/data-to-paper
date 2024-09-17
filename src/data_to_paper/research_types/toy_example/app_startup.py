from data_to_paper.interactive.base_app_startup import DataFilesStartDialog, TextEditWithHeader, SingleFileWidget


class ToyStartDialog(DataFilesStartDialog):
    def _set_style(self):
        super()._set_style()
        self.resize(600, 500)

    def _create_widgets(self):
        return {
            'research_goal': TextEditWithHeader(
                "Research Goal", "Specify a funny research goal.", on_change=self.update_start_button_state),
            'files_widget': SingleFileWidget(on_change=self.update_start_button_state),
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

    def _get_mandatory_items_to_start(self):
        research_goal_filled = bool(self.widgets['research_goal'].toPlainText().strip())
        files_filled = any(file_widget.abs_path and file_widget.description_edit.toPlainText().strip()
                           for file_widget in self._get_date_files_widget().get_all_file_widgets())

        return research_goal_filled, files_filled
