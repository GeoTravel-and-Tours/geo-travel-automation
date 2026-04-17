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
- **Timestamp:** `2026-04-17_07-25-26`
- **Link:** [2026-04-17_07-25-26](2026-04-17_07-25-26/)
- **Reports:** 4
- **API Response Dumps:** 56
- **Test Logs:** 99
- **Screenshots:** 106
- **Status:** ⚠️ Had failures

### 📂 Recent Runs (Last 10)
- **[2026-04-17_07-25-26](2026-04-17_07-25-26/)** – 4 reports, 99 logs, 56 API dumps, 106 screenshots ⚠️
- [2026-04-16_07-24-50](2026-04-16_07-24-50/) – 4 reports, 99 logs, 55 API dumps, 106 screenshots ⚠️
- [2026-04-15_07-23-40](2026-04-15_07-23-40/) – 3 reports, 61 logs, 4 API dumps, 106 screenshots ⚠️
- [2026-04-14_07-23-30](2026-04-14_07-23-30/) – 3 reports, 61 logs, 4 API dumps, 106 screenshots ⚠️
- [2026-04-13_07-55-11](2026-04-13_07-55-11/) – 3 reports, 61 logs, 4 API dumps, 106 screenshots ⚠️
- [2026-04-12_07-07-41](2026-04-12_07-07-41/) – 3 reports, 61 logs, 4 API dumps, 106 screenshots ⚠️
- [2026-04-11_06-55-30](2026-04-11_06-55-30/) – 3 reports, 61 logs, 4 API dumps, 106 screenshots ⚠️
- [2026-04-10_07-20-20](2026-04-10_07-20-20/) – 3 reports, 61 logs, 4 API dumps, 106 screenshots ⚠️
- [2026-04-09_07-15-30](2026-04-09_07-15-30/) – 3 reports, 67 logs, 4 API dumps, 20 screenshots ⚠️
- [2026-04-08_07-11-14](2026-04-08_07-11-14/) – 3 reports, 67 logs, 4 API dumps, 20 screenshots ⚠️

_Last updated: Fri Apr 17 07:37:27 UTC 2026_

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
