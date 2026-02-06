PYTHON_CMD  := uv run python3 -m src --output ol.json

BOLD   := \033[1m
RESET  := \033[0m
GREEN  := \033[32m

.PHONY: all install run debug clean lint lint-strict


all: install run

install:
	@echo "$(BOLD)🚀 Initializing project environment and syncing dependencies...$(RESET)"
	@pip install uv
	@uv sync
	@echo "\n$(BOLD)$(GREEN)✅ Environment setup complete.$(RESET)"

run:
	@echo "$(BOLD)🕹️  Executing main script...$(RESET)"
	$(PYTHON_CMD) $(CONFIG_FILE)

debug:
	@echo "$(BOLD)⚙️ Executing main script with pdb...$(RESET)"
	$(PYTHON_CMD) -m pdb $(MAIN_SCRIPT) $(CONFIG_FILE)

clean:
	@echo "$(BOLD)🗑️  Cleaning up build artifacts and cache...$(RESET)"
	rm -rf .mypy_cache src/__pycache__ llm_sdk/__pycache__
	@echo "\n$(BOLD)$(GREEN)🧹 Workspace is clean.$(RESET)"

lint:
	@echo "$(BOLD)🔎 Running static code analysis...$(RESET)"
	flake8 . --exclude=.venv,llm_sdk/__init__.py
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@echo "$(BOLD)🔎 Running static code analysis (strict option)...$(RESET)"
	flake8 . --exclude=.venv,llm_sdk/__init__.py
	mypy . --strict
