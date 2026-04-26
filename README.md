# GeoTravel QA Test Results (GitHub Pages)

This branch (`gh-pages`) contains **automatically generated QA test artifacts** for the **GeoTravel Automation** project, published via **GitHub Pages**.

🌐 **Live Dashboard:**  
https://geotravel-and-tours.github.io/geo-travel-automation/

>  ‎
> ⚠️ **Important:**  
> This is a **deployment/output branch**, not a development branch.  
> All files here are generated and committed by GitHub Actions.
>  ‎

---

## 📌 Purpose of This Branch

The `gh-pages` branch exists to:

- Publish QA test results publicly
- Preserve **historical test runs**
- Provide a lightweight **QA dashboard**
- Keep large test artifacts **out of `main`**

No application logic lives here.

---

## 🧪 What Gets Published

Each test execution creates a **timestamped folder** containing all artifacts for that run.

### Example Run Folder

#### Folder Structure
```
2026-01-01_07-14-22/
├── index.html
├── api_failed_responses/
├── logs/
├── reports/
└── screenshots/
```

### Root Files
**index.html**  - # Main dashboard (latest run)
**README_TEMPLATE** file  - # This documentation

---

## 🏠 Main Dashboard (`index.html`)

The root `index.html` provides:

- A clean UI showing the **latest test run**
- A direct link to that run's artifacts
- Simple navigation with zero dependencies

This file is **regenerated on every successful workflow run**.

---

<!-- AUTO-GENERATED:START -->

## 📊 Test Results Status

### 🕒 Latest Run
- **Timestamp:** `2026-04-26_06-59-48`
- **Link:** [2026-04-26_06-59-48](2026-04-26_06-59-48/)
- **Reports:** 4
- **API Response Dumps:** 41
- **Test Logs:** 157
- **Screenshots:** 13
- **Status:** ⚠️ Had failures

### 📂 Recent Runs (Last 10)
- **[2026-04-26_06-59-48](2026-04-26_06-59-48/)** – 4 reports, 157 logs, 41 API dumps, 13 screenshots ⚠️
- [2026-04-25_06-20-54](2026-04-25_06-20-54/) – 4 reports, 157 logs, 43 API dumps, 13 screenshots ⚠️
- [2026-04-24_07-05-02](2026-04-24_07-05-02/) – 4 reports, 157 logs, 41 API dumps, 13 screenshots ⚠️
- [2026-04-23_07-01-47](2026-04-23_07-01-47/) – 3 reports, 119 logs, 7 API dumps, 4 screenshots ⚠️
- [2026-04-22_06-58-02](2026-04-22_06-58-02/) – 4 reports, 157 logs, 41 API dumps, 3 screenshots ⚠️
- [2026-04-21_07-27-31](2026-04-21_07-27-31/) – 2 reports, 38 logs, 1 API dumps, 30 screenshots ⚠️
- [2026-04-20_07-58-24](2026-04-20_07-58-24/) – 4 reports, 157 logs, 40 API dumps, 15 screenshots ⚠️
- [2026-04-19_07-12-05](2026-04-19_07-12-05/) – 4 reports, 99 logs, 54 API dumps, 106 screenshots ⚠️
- [2026-04-18_07-01-05](2026-04-18_07-01-05/) – 4 reports, 99 logs, 55 API dumps, 106 screenshots ⚠️
- [2026-04-17_07-25-26](2026-04-17_07-25-26/) – 4 reports, 99 logs, 56 API dumps, 106 screenshots ⚠️

_Last updated: Sun Apr 26 07:16:05 UTC 2026_

<!-- AUTO-GENERATED:END -->

---

## ⚙️ How This Branch Is Updated

Updates to this branch are **fully automated** by GitHub Actions.

### Trigger Conditions
- Push to `main`
- Daily scheduled run (`07:00 UTC`)
- Manual workflow dispatch

### Automation Flow
1. Test suites are executed:
   - Smoke tests
   - API tests
   - Partners API tests
2. Artifacts are collected:
   - Logs
   - Reports
   - Failed API responses
   - Screenshots (for failures)
3. A timestamped folder is created
4. HTML indexes are generated
5. Files are committed and pushed to `gh-pages`

➡️ **No manual deployment is required.**

---

## 🚫 Branch Rules (Strict)

Do **NOT** do the following:

- ❌ Manually edit files in this branch
- ❌ Commit directly from a local machine
- ❌ Force-push
- ❌ Delete historical runs

All changes must originate from:
- GitHub Actions
- Test scripts
- CI configuration

If something looks wrong here, **fix the pipeline**, not this branch.

---

## 🧠 Why This Approach Was Chosen

- GitHub Pages provides **free, reliable hosting**
- Timestamped runs ensure **auditability**
- `keep_files: true` preserves test history
- Separating artifacts prevents repo pollution
- HTML output avoids tooling lock-in

This setup scales cleanly as test coverage grows.

---

## 👤 Maintainer

[Adeniyi John Busayo](https://www.linkedin.com/in/john-adeniyi/)
QA Automation Engineer

Generated with ❤️ by GitHub Actions

---

## 📎 Related Branches

- `main` → Test source code & workflows
- `gh-pages` → Published QA artifacts (this branch)

---

## 📝 Notes

If you are reading this file in the GitHub UI:

- The **live test results** are best viewed via the GitHub Pages URL
- Some reports are large and may take a moment to load
