import json
import os


class ObjectRepository:

    def __init__(self, file_path="data/object_repository.json"):
        self.file_path = file_path
        self.repository = self._load_repository()

    def _load_repository(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(
                f"Object Repository not found: {self.file_path}"
            )

        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get_element(self, url, element_name):
        try:
            return self.repository[url]["elements"][element_name]
        except KeyError:
            raise KeyError(
                f"Element '{element_name}' not found for URL '{url}'"
            )

    def get_locator(self, url, element_name):
        element = self.get_element(url, element_name)

        locator_type = element["locator_type"]
        locator = element["locator"]

        return locator_type, locator