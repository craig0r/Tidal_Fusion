# Contributing to Tidal Fusion

Thank you for your interest in contributing to Tidal Fusion! We welcome contributions from the community to help make this tool better.

## Reporting Issues
If you encounter a bug or have a feature request, please use the GitHub Issue Tracker.

### Bug Reports
When reporting a bug, please include:
- Your OS and Python version.
- The command you ran (e.g., `tidal-fusion --mode flow -n`).
- The output or error message (please redact any personal tokens/IDs).
- Detailed steps to reproduce the issue.

### Feature Requests
We'd love to hear your ideas! Please describe:
- The problem you are trying to solve.
- Your proposed solution or feature.
- Any alternatives you've considered.

## Development

### Setting Up
1. Fork the repository.
2. Clone your fork locally.
   ```bash
   git clone https://github.com/YOUR_USERNAME/Tidal_Fusion.git
   cd Tidal_Fusion
   ```
3. Create a virtual environment and install dependencies.
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

### Pull Requests
1. Create a new branch for your feature or fix.
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Make your changes and test thoroughly.
3. Commit your changes with clear, descriptive messages.
4. Push to your fork and submit a Pull Request to the `main` branch.

## Code Style
- Follow PEP 8 guidelines for Python code.
- Ensure your changes do not break existing functionality (run basic mode tests).
- Update documentation (`USAGE.md`, `README.md`) if you change CLI arguments or behavior.
