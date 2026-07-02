# Smartwave Python API
The API talks to the device over its **USB-serial command protocol** — the same binary
protocol the browser WebGUI uses (the API does not need the browser). It is historically
named the "WebGUI-Arduino-protocol"; on the firmware side this is `MODE_USB_SERIAL`
(formerly "WebGUI mode").

## Updating the register map (`fpga_reg`) — FIRST step of any API update
`examples/fpga_reg.py` is a generated copy of the FPGA register map. Before anything else
when updating the API against a new FPGA, regenerate it:

In `wfg-fpga/templating` run `make python`. It templates the register map **in place**
from the register CSV/JSONs into every repo that
uses it in one go: the 'original'' `wfg-fpga/firmware/scripts/fpga_reg.py` **and** the
vendored copies `wfg-API/examples/fpga_reg.py` + `SmartWave-Demos/common/fpga_reg.py`
(each is updated only if that repo is a sibling of `wfg-fpga`; missing ones are skipped, so the target never fails for an absent consumer repo).

## Publishing
> This is the **API / PyPI slice** of the release. The full cross-repo release flow — staging the
> firmware + FPGA bitstream into this package, and the order/tags across all repos — lives in
> [`wfg-arduino/Release.md`](../wfg-arduino/Release.md); the API publish is done **last**, after the
> binaries are staged.

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

Finally, commit the version bump (with any updated binaries) and **tag the release** — a lightweight
tag named `X.Y.Z` to match the `pyproject.toml` version (no `v` prefix), consistent with the other repos:
```bash
git commit -am "release <version>"
git tag <version>
git push && git push origin <version>
```