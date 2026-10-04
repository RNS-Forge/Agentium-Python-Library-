# Agentium v2.0.0 Deployment & Packaging Commands

## 1. Environment Preparation
```bash
python -m pip install --upgrade pip build twine
```

## 2. Test & Compliance Verification
```bash
# Check zero third-party runtime dependencies
python test/v2/test_zero_deps.py

# Run Agentium v2 master test suite (27 suites)
python test/v2/run_all_v2_tests.py

# Run Agentium v1 backward-compatibility test suite (14 suites)
python test/v1/run_all_tests.py
```

## 3. Package Build
```bash
# Clean previous build artifacts
python -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('build', 'dist', 'src/agentium.egg-info')]"

# Build distribution packages
python -m build
```

## 4. Package Validation
```bash
# Validate distribution integrity with Twine
python -m twine check dist/*
```

## 5. Upload to TestPyPI (Staging)
```bash
python -m twine upload --repository testpypi dist/*
```

## 6. TestPyPI Installation Test
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentium==2.0.0
```

## 7. Upload to Production PyPI
```bash
# Set authentication token
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="your-pypi-api-token"

# On Windows PowerShell:
# $env:TWINE_USERNAME="__token__"
# $env:TWINE_PASSWORD="your-pypi-api-token"

# Upload to production PyPI
python -m twine upload dist/*
```

## 8. Production Verification
```bash
pip install agentium==2.0.0
agentium doctor
```