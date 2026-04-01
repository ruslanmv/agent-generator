# Release Process

## Steps

1. Run lint: `ruff check src/`
2. Run tests: `pytest tests/ -v`
3. Build: `python -m build`
4. Verify wheel: `pip install dist/*.whl`
5. Tag: `git tag v0.2.1`
6. Publish: `twine upload dist/*`

## Version locations

- `pyproject.toml` — package version
- `src/agent_generator/__init__.py` — runtime version
- `src/agent_generator/cli.py` — CLI version display
- `build_service.py` — manifest generator_version
