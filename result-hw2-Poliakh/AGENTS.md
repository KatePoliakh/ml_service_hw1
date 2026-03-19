# AGENTS.md

## Agent Development Rules

1. Always follow FEATURE_PLAN_MODEL_EVALUATION.md step-by-step.
2. After each code modification:
   - Run ruff
   - Fix lint issues
3. After implementing logic:
   - Run pytest
4. Use type hints in all functions.
5. Follow PEP8.
6. Do not modify unrelated files.
7. Update documentation:
   - API.md
   - CHANGELOG.md
8. Keep code modular.
9. Use clear naming.
10. Never skip plan steps.