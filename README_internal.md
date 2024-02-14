# Smartwave Python API

Design goals:
   - Stage 1: Aid in development and debugging
   - Stage 2: Supplement the Webgui


The API should follow the WebGUI Communication protocol as outlined here:
https://github.com/semify-eda/wfg-webgui/blob/main/doc/WebGUI-Arduino-protocol.md

## Publishing
(Only once) To publish, all the requirements in the root `requirements.txt` have to be installed:
```bash
pip install -r requirements.txt
```
Update the version number in `pyproject.toml`, then build:
```bash
python -m build
```
To upload to TestPyPi (for further information how to set up twine, see [this tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/#uploading-the-distribution-archives)):
```bash
python -m twine upload --skip-existing --repository testpypi dist/*
```
To upload to production PyPi:
```bash
python -m twine upload --skip-existing dist/*
```