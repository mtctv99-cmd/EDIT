from .settings import Settings

class PromptStore:
    @staticmethod
    def list_prompts() -> list:
        return Settings.load_prompts()

    @staticmethod
    def save_prompts(prompts: list):
        Settings.save_prompts(prompts)
