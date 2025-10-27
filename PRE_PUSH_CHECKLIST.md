## ✅ `Pre-Push Checklist`

This checklist helps ensure code and configurations are clean, consistent, and ready before pushing changes to the repository.

---

## 1. Code & Structure

- [ ] All recent code changes are **committed**.
- [ ] Unused imports or debug statements (e.g., `print()`, `pdb`, `breakpoint()`) are removed.
- [ ] File names and directories follow the existing project structure.
- [ ] All test files are inside the appropriate folders (`smoke_tests`, `regression_tests`, etc.).
- [ ] Sensitive information (API keys, credentials, etc.) is **not** exposed in code or logs.

---

## 2. Tests & Reports

- [ ] All **smoke and regression tests** pass locally.
- [ ] Test reports (HTML/JSON) are **generated and reviewed**.
- [ ] Screenshots and logs are saved correctly (if applicable).
- [ ] Any new test has clear and meaningful assertions.
- [ ] ⚠️ **Update `_get_test_context()` in `reporting.py`** with any new test names to keep Slack report context accurate.

---

## 3. Configuration Files

- [ ] `.env` and `configs/` files are updated with correct values.
- [ ] Default or placeholder values are not left in production configs.
- [ ] Any new configuration keys are documented in the README or ENV example.

---

## 4. Documentation

- [ ] `README.md` reflects recent structural or command changes (if any).
- [ ] `CHANGELOG.md` has been updated with new features, fixes, or improvements.

---

## 5. Git & Version Control

- [ ] Branch name follows the naming convention (e.g., `feature/...`, `fix/...`, `test/...`).
- [ ] Commits are clear and descriptive.
- [ ] Merge conflicts are resolved before pushing.
- [ ] The project runs successfully after a clean clone.

---

## 6. Integration

- [x] CI/CD pipeline configurations updated (`.circleci`).
- [x] Notifications (Slack, email, etc.) tested successfully.
- [x] Environment URLs or endpoints verified.

---

**Tip:**  
***[GIT-IGNORED]*** Run the following command to auto-fix issues where possible:
- Formatting issues *(Black)*
- Style & logic errors *(Flake8)*
- Deep quality suggestions *(Pylint)*
- Security warnings *(Bandit)*
- Unified lint report *(Ruff)*

```bash
bash scripts/code_audit.sh
```