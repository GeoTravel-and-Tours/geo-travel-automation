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
- **Timestamp:** `2026-06-28_08-22-17`
- **Link:** [2026-06-28_08-22-17](2026-06-28_08-22-17/)
- **Reports:** 3
- **API Response Dumps:** 0
- **Test Logs:** 118
- **Screenshots:** 3
- **Status:** ⚠️ Had failures

### 📂 Recent Runs (Last 10)
- **[2026-06-28_08-22-17](2026-06-28_08-22-17/)** – 3 reports, 118 logs, 3 screenshots ⚠️
- [2026-06-27_07-50-33](2026-06-27_07-50-33/) – 3 reports, 118 logs, 4 screenshots ⚠️
- [2026-06-26_08-30-35](2026-06-26_08-30-35/) – 3 reports, 118 logs, 28 screenshots ⚠️
- [2026-06-25_08-23-52](2026-06-25_08-23-52/) – 3 reports, 118 logs, 1 screenshots ⚠️
- [2026-06-24_08-22-54](2026-06-24_08-22-54/) – 3 reports, 118 logs, 2 screenshots ⚠️
- [2026-06-23_08-29-55](2026-06-23_08-29-55/) – 3 reports, 118 logs, 2 screenshots ⚠️
- [2026-06-22_10-39-37](2026-06-22_10-39-37/) – 3 reports, 118 logs, 3 screenshots ⚠️
- [2026-06-21_08-57-40](2026-06-21_08-57-40/) – 3 reports, 118 logs, 1 screenshots ⚠️
- [2026-06-20_08-22-11](2026-06-20_08-22-11/) – 3 reports, 118 logs, 1 screenshots ⚠️
- [2026-06-19_09-28-18](2026-06-19_09-28-18/) – 3 reports, 118 logs, 1 screenshots ⚠️

_Last updated: Sun Jun 28 08:37:10 UTC 2026_

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
