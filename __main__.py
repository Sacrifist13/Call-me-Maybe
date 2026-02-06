from .reader import Reader

if __name__ == "__main__":
    reader = Reader(True)
    validated_data = reader.load_validated_data()

    # for prompt_file in validated_data["prompt"]:
    #     print(prompt_file)
    # for definition in validated_data["function"]:
    #     print(definition)
