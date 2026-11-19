UV ?= uv

.PHONY: install
# target: install - Set up the environment and the git hooks
i install:
	$(UV) sync
	$(UV) run pre-commit install

.PHONY: test
# target: test - Runs tests
t test: install
	@$(UV) run pytest

.PHONY: types
# target: types - Type checking
types: install
	@$(UV) run pyrefly check
	@$(UV) run pyrefly coverage check

VERSION	?= minor

.PHONY: version
version: install
	$(UV) version --bump $(VERSION)
	git commit -am "build(version): $$($(UV) version --short)"
	git checkout main
	git pull
	git merge develop
	git checkout develop
	git push origin develop main
	git tag "$$($(UV) version --short)"
	git push origin "refs/tags/$$($(UV) version --short)"

.PHONY: minor patch major
minor patch major:
	$(MAKE) version VERSION=$@

.PHONY: clean
# target: clean - Display callable targets
clean:
	rm -rf build/ dist/ docs/_build *.egg-info
	find $(CURDIR) -name "*.py[co]" -delete
	find $(CURDIR) -name "*.orig" -delete
	find $(CURDIR) -name "__pycache__" | xargs rm -rf
