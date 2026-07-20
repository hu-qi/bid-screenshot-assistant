.PHONY: install test check demo serve

install:
	python -m pip install -e '.[dev]'

test:
	pytest

check:
	python -m compileall src skills
	pytest

demo:
	bid-screenshot demo --query "广州市某智慧园区项目"

serve:
	uvicorn bid_screenshot_assistant.api:app --reload
