from .reader import Reader
from .generator import VocabularyHandler

if __name__ == "__main__":
    reader = Reader(True)
    vh = VocabularyHandler()

    validated_data = reader.load_validated_data()
    vh.load_vocabulary()

    vh.test("Fais un prout")
