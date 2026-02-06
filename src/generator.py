import json
from llm_sdk import Small_LLM_Model
from .tools import print_err


class VocabularyHandler:
    def __init__(self) -> None:
        self.llm = Small_LLM_Model()

    def load_vocabulary(self) -> None:
        try:
            with open(self.llm.get_path_to_vocabulary_json(), "r") as f:
                self.vocabulary = json.loads(f.read())
        except Exception as e:
            print_err(str(e))


# Pour chaque prompt ->
#   - J'envoie le prompt
#   - Si le token contient en premier un "[" alors je ne le mets pas a - inf
#   - Si le token contient ensuite un "{" alors je ne le mets pas a -inf
#   - 
