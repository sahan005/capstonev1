# Capstone Milestone 1 (V1) - E-Commerce Test Automation Script

An end-to-end automated test script built with Python and Selenium WebDriver against the OpenCart demo storefront (`https://tutorialsninja.com/demo/`).

---

## 1. Tech Stack (V1)

- **Language**: Python 3.10+ (tested on Python 3.14)
- **Automation Engine**: Selenium WebDriver 4.x
- **Test Runner**: pytest 8.x / 9.x
- **Driver Management**: webdriver-manager (automatic ChromeDriver resolution, zero hardcoded paths)
- **Test Data**: JSON (`test_data/data.json`) and Excel (`test_data/data.xlsx` via `openpyxl`)
- **Reporting**: pytest-html (`--self-contained-html`)
- **Logging**: Python standard `logging` module (Console output + `reports/test_execution.log`)

---

## 2. 1:1 Mapping to Functional Requirements

The test script in [`test_ecommerce_v1.py`](test_ecommerce_v1.py) explicitly implements all 10 numbered requirements with `# STEP n:` markers:

| Step # | Requirement | Implementation Details |
| :--- | :--- | :--- |
| **STEP 1** | **Launch Browser** | Chrome launched via `webdriver-manager` without hardcoded driver paths; maximized window; implicit wait (5s) + explicit `WebDriverWait` (10s) with `expected_conditions`; zero `time.sleep()`. |
| **STEP 2** | **Login & Auto-Register** | Navigates to *My Account → Login*. Checks if account exists; if not yet registered (`is_registered: false`), auto-registers a new account using data from the test data file, saves credentials back to `data.json` and `data.xlsx` so re-runs reuse the account, and logs in. |
| **STEP 3** | **Search Product** | Uses top search bar (`name='search'`) to query product name (`"MacBook"`) from test data. Submits via Enter key. |
| **STEP 4** | **Add Product to Cart** | Opens product details from search results, clicks *Add to Cart* (`#button-cart`), asserts and verifies the `.alert-success` banner ("*Success: You have added Product to your shopping cart!*"). |
| **STEP 5** | **Update Quantity** | Navigates to Shopping Cart page, changes quantity (e.g., `1` → `3`), clicks Update button (`button[type='submit']`), and waits for update confirmation. |
| **STEP 6** | **Verify Cart Details** | Asserts product name matches, updated quantity matches target, extracts unit price and line total, and validates `unit_price × quantity == line_total`. Fails test loudly and clearly if any mismatch occurs. |
| **STEP 7** | **Capture Screenshots** | Captured after each major step (`post-login`, `post-search`, `post-add-to-cart`, `post-update`, `final-cart`) and saved to `screenshots/<timestamp>_<step_name>.png`. |
| **STEP 8** | **Read Test Data from Excel/JSON** | Uses [`utils/data_reader.py`](utils/data_reader.py) to read and synchronize credentials and product information from `data.json` and `data.xlsx`. |
| **STEP 9** | **Handle Popups/Alerts Defensively** | `handle_popups_and_alerts()` defensively handles JS alerts/prompts, cookie consent banners, and modal dialogs without failing if they do not appear. |
| **STEP 10** | **Generate Execution Report** | Generates a standalone, self-contained HTML report with pass/fail status and execution logs using `pytest --html=reports/report.html --self-contained-html`. |

---

## 3. Directory Structure

```text
capstone_v1/
├── test_data/
│   ├── data.xlsx          # Excel test data (UserCredentials & ProductData sheets)
│   └── data.json          # JSON test data alternative
├── screenshots/           # Step-by-step timestamped screenshots
├── reports/
│   ├── report.html        # Standalone HTML execution report
│   └── test_execution.log # Test execution logs
├── utils/
│   └── data_reader.py     # Data reader supporting both JSON and Excel
├── test_ecommerce_v1.py   # Main pytest automation script (Steps 1–10)
├── requirements.txt       # Project dependencies
└── README.md              # Documentation and execution guide
```

---

## 4. Setup and Installation

### 4.1 Prerequisites
- Python 3.10 or higher
- Google Chrome browser installed

### 4.2 Create and Activate Virtual Environment

From the project root:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# Windows (Command Prompt):
.\.venv\Scripts\activate.bat

# Linux / macOS:
source .venv/bin/activate
```

### 4.3 Install Dependencies

```bash
pip install -r capstone_v1/requirements.txt
```

---

## 5. Execution Guide

You can run the automation script directly with Python:

```bash
python test_ecommerce_v1.py
```

Or using pytest:

```bash
pytest test_ecommerce_v1.py --html=reports/report.html --self-contained-html -v -s
```

Either command will:
1. Launch Chrome automatically via `webdriver-manager`
2. Execute all 10 functional test steps
3. Save screenshots into `screenshots/`
4. Generate the standalone HTML report at `reports/report.html`


---

## 6. Output Artifacts

- **HTML Report**: `capstone_v1/reports/report.html` (Open in any web browser)
- **Execution Log**: `capstone_v1/reports/test_execution.log`
- **Screenshots**: `capstone_v1/screenshots/`
  - `<timestamp>_post_login.png`
  - `<timestamp>_post_search.png`
  - `<timestamp>_post_add_to_cart.png`
  - `<timestamp>_post_update.png`
  - `<timestamp>_final_cart.png`
