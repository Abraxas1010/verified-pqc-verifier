# Build And Release

Build the ML-DSA verifier backend:

```bash
bash scripts/build_dsa_open_cli.sh
```

Install the Python package locally:

```bash
python3 -m pip install -e .
```

Run the sample verification flow:

```bash
./scripts/verify_all.sh
```

Build release artifacts:

```bash
./scripts/build_release_artifacts.sh
```

Smoke the release as an installed wheel plus unpacked verifier asset bundle:

```bash
./scripts/smoke_release_artifacts.sh
```
