from PySide6.QtCore import QObject, Signal
import litellm


class ModelManager(QObject):
    """
    Manages available models and the currently selected model.
    Implemented as a singleton so that every part of the application
    (both UI and server code) refer to the same model selection.
    """

    modelChanged = Signal(str)  # Emits the new model name when changed

    _instance = None

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = ModelManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        # Get all models from litellm and filter for chat models.
        self.all_models = litellm.utils.get_valid_models()
        self.chat_models = self._filter_chat_models(self.all_models)
        # Default to the first chat model if available.
        self._current_model = self.chat_models[0] if self.chat_models else None

    def _filter_chat_models(self, models: list) -> list:
        chat_models = []
        for model in models:
            try:
                info = litellm.get_model_info(model)
                if info.get("mode") == "chat":
                    chat_models.append(model)
            except Exception:
                continue
        return chat_models

    def refresh_models(self):
        """Refresh the available models and update the chat models list."""
        self.all_models = litellm.utils.get_valid_models()
        self.chat_models = self._filter_chat_models(self.all_models)
        if self._current_model not in self.chat_models and self.chat_models:
            self.set_current_model(self.chat_models[0])

    def get_all_models(self) -> list:
        return self.all_models

    def get_chat_models(self) -> list:
        return self.chat_models

    def get_current_model(self) -> str:
        return self._current_model

    def set_current_model(self, model: str):
        """
        Update the current model.
        If the new model is different, update and emit a signal.
        """
        if model != self._current_model:
            self._current_model = model
            self.modelChanged.emit(model)

    def __str__(self):
        return f"Current Model: {self._current_model}\nAvailable Chat Models: {self.chat_models}"
