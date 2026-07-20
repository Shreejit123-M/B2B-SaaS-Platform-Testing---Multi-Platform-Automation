# WorkFlow Pro QA Automation Framework

A production-grade test automation framework for the WorkFlow Pro B2B SaaS platform, supporting web browsers, mobile devices, and cross-platform testing via BrowserStack.

## 📋 Project Overview

This repository implements a comprehensive test automation solution for the WorkFlow Pro project management platform, addressing:

- **Multi-tenant SaaS testing** with tenant isolation validation
- **Cross-platform support** (Chrome, Firefox, Safari, iOS, Android)
- **Hybrid test approach** (API + UI + Mobile integration)
- **CI/CD pipeline integration** with GitHub Actions
- **Enterprise-grade reporting** with Allure and pytest-html

### Tech Stack

- **Python 3.11+** - Core automation language
- **Pytest** - Test framework with fixtures and plugins
- **Playwright (Sync API)** - Browser automation
- **Requests** - HTTP API testing
- **BrowserStack** - Cross-platform cloud testing
- **Allure** - Advanced test reporting
- **pytest-html** - HTML test reports
- **python-dotenv** - Environment configuration management

## 🏗️ Architecture

### Design Patterns

- **Page Object Model (POM)** - Abstraction layer for UI interactions
- **Fixture-based setup/teardown** - Reusable test data and fixtures
- **API Client pattern** - Centralized HTTP request handling
- **Strategy pattern** - Multiple browser/platform configurations
- **Builder pattern** - Test data construction

### Framework Layers

```
Tests (pytest)
    ↓
Page Objects + API Clients (POM + Requests)
    ↓
Core Base Classes (WebDriver, Waiter, Logging)
    ↓
Configuration & Fixtures (Environments, Browsers, Test Data)
    ↓
BrowserStack / Local Browsers / Mobile
```

## 📁 Repository Structure

```
.
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Pytest configuration
├── .gitignore                     # Git ignore rules
├── .env.example                   # Example environment variables
│
├── docs/                          # Documentation
│   ├── Test_Plan.md              # Comprehensive test plan and coverage
│   ├── Framework_Design.md       # Architecture and design decisions
│   ├── Assumptions.md            # Implementation assumptions
│   └── FLAKY_TEST_ANALYSIS.md   # Part 1: Flaky test debugging
│
├── config/                        # Configuration modules
│   ├── __init__.py
│   ├── environments.py            # Environment configuration
│   ├── browsers.py                # Browser capabilities
│   ├── browserstack.py            # BrowserStack setup
│   └── test_data.py              # Test data constants
│
├── core/                          # Core framework classes
│   ├── __init__.py
│   ├── base_page.py              # Page Object base class
│   ├── base_test.py              # Test base class
│   ├── api_client.py             # HTTP client wrapper
│   ├── waiter.py                 # Custom wait mechanisms
│   └── exceptions.py             # Custom exceptions
│
├── pages/                         # Page Object Models
│   ├── __init__.py
│   ├── login_page.py             # Login page POM
│   ├── dashboard_page.py         # Dashboard page POM
│   ├── projects_page.py          # Projects listing page POM
│   └── project_details_page.py   # Project details page POM
│
├── api/                           # API client classes
│   ├── __init__.py
│   ├── auth_api.py               # Authentication endpoints
│   ├── projects_api.py           # Projects endpoints
│   └── users_api.py              # Users endpoints
│
├── fixtures/                      # Pytest fixtures
│   ├── __init__.py
│   ├── browser_fixtures.py       # Browser initialization
│   ├── auth_fixtures.py          # Authentication fixtures
│   └── data_fixtures.py          # Test data fixtures
│
├── utils/                         # Utility functions
│   ├── __init__.py
│   ├── logger.py                 # Logging configuration
│   ├── helpers.py                # Helper functions
│   └── data_generator.py         # Test data generation
│
├── tests/                         # Test suites
│   ├── conftest.py               # Global pytest configuration
│   ├── web/                      # Web UI tests
│   │   ├── conftest.py
│   │   ├── test_authentication.py
│   │   ├── test_dashboard.py
│   │   ├── test_projects.py
│   │   └── test_multi_tenant.py
│   ├── api/                      # API tests
│   │   ├── conftest.py
│   │   ├── test_auth_api.py
│   │   ├── test_projects_api.py
│   │   └── test_users_api.py
│   ├── integration/              # Integration tests
│   │   ├── conftest.py
│   │   ├── test_project_creation_flow.py  # Part 3: Main flow
│   │   ├── test_cross_platform.py
│   │   └── test_user_workflow.py
│   └── mobile/                   # Mobile-specific tests
│       ├── conftest.py
│       ├── test_mobile_projects.py
│       ├── test_mobile_navigation.py
│       └── test_mobile_responsiveness.py
│
├── reports/                       # Generated reports (gitignored)
│
├── browserstack/                  # BrowserStack related files
│   └── bs_config.json            # BrowserStack configuration
│
└── .github/                       # GitHub specific files
    └── workflows/
        └── ci.yml                # CI/CD pipeline
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Shreejit123-M/B2B-SaaS-Platform-Testing---Multi-Platform-Automation.git
   cd B2B-SaaS-Platform-Testing---Multi-Platform-Automation
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

5. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Environment Configuration

Create a `.env` file with:

```env
# Application Configuration
APP_BASE_URL=https://app.workflowpro.com
APP_LOGIN_URL=https://app.workflowpro.com/login
APP_API_BASE_URL=https://api.workflowpro.com

# Test Accounts (Multi-tenant)
ADMIN_EMAIL=admin@company1.com
ADMIN_PASSWORD=<secure_password>
COMPANY1_USER_EMAIL=user@company1.com
COMPANY1_USER_PASSWORD=<secure_password>
COMPANY2_USER_EMAIL=user@company2.com
COMPANY2_USER_PASSWORD=<secure_password>

# API Configuration
API_TOKEN=<bearer_token>
X_TENANT_ID=company1

# BrowserStack Configuration
BROWSERSTACK_ENABLED=false
BROWSERSTACK_USERNAME=<your_username>
BROWSERSTACK_ACCESS_KEY=<your_key>

# Execution Configuration
HEADLESS=true
BROWSER=chromium  # chromium, firefox, webkit
MOBILE_DEVICE=  # Leave empty for desktop, or: "iPhone 12", "Pixel 5"

# Logging
LOG_LEVEL=INFO
SCREENSHOT_ON_FAILURE=true
TRACE_ON_FAILURE=true
```

## 🧪 Test Execution

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Web UI tests
pytest tests/web/ -v

# API tests
pytest tests/api/ -v

# Integration tests
pytest tests/integration/ -v

# Mobile tests
pytest tests/mobile/ -v
```

### Run with Specific Markers

```bash
# Critical tests only
pytest -m critical

# Smoke tests
pytest -m smoke

# Exclude slow tests
pytest -m "not slow"

# Multi-tenant tests
pytest -m multi_tenant
```

### Run with Headless Browser

```bash
HEADLESS=true pytest tests/web/ -v
```

### Run with Specific Browser

```bash
BROWSER=firefox pytest tests/web/ -v
BROWSER=webkit pytest tests/web/ -v
```

### Run with Mobile Emulation

```bash
MOBILE_DEVICE="iPhone 12" pytest tests/mobile/ -v
```

### Generate Reports

```bash
# HTML Report
pytest --html=reports/report.html --self-contained-html

# Allure Report
pytest --alluredir=reports/allure-results
allure serve reports/allure-results
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4
```

## 📊 Test Coverage

### Part 1: Flaky Test Debugging
- Identified 12+ flakiness issues in provided tests
- Root cause analysis for CI/CD vs local environments
- Rewritten with best practices:
  - Explicit waits with Playwright `expect()`
  - Dynamic element loading handling
  - 2FA flow assumptions
  - Network resilience
  - See `docs/FLAKY_TEST_ANALYSIS.md`

### Part 2: Framework Design
- Scalable architecture supporting 100+ test cases
- POM pattern with inheritance
- Pytest fixtures for DRY setup/teardown
- Configuration management for multi-environments
- BrowserStack integration strategy
- Comprehensive logging and reporting
- See `docs/Framework_Design.md`

### Part 3: Integration Testing
- End-to-end project creation flow
- API → Web UI → Mobile verification
- Tenant isolation validation
- Cross-platform testing strategy
- Test data lifecycle management
- See `tests/integration/test_project_creation_flow.py`

## 🔧 Configuration Management

### Environment Handling

The framework supports multiple environments via the `config/environments.py` module:

- **Local** - Local browser execution
- **Staging** - Staging environment
- **Production** - Production environment (for API tests only)
- **CI** - GitHub Actions CI environment

### Browser Capabilities

Defined in `config/browsers.py`:
- Chrome (desktop & mobile)
- Firefox
- Safari (WebKit)
- iOS (via BrowserStack)
- Android (via BrowserStack)

### BrowserStack Integration

Configure in `.env`:
```env
BROWSERSTACK_ENABLED=true
BROWSERSTACK_USERNAME=your_username
BROWSERSTACK_ACCESS_KEY=your_key
```

**Cost Optimization**: Tests run locally by default; BrowserStack used for:
- Safari testing (not available locally)
- Real mobile devices (iOS/Android)
- Cross-browser CI validation

## 📈 Reporting

### HTML Reports
```bash
pytest --html=reports/report.html --self-contained-html
```
Includes:
- Test results summary
- Duration tracking
- Failure screenshots
- Test details and stack traces

### Allure Reports
```bash
pytest --alluredir=reports/allure-results
allure serve reports/allure-results
```
Features:
- Visual test trends
- Detailed execution history
- Issue tracking
- Timeline view

### Screenshots & Artifacts
- Automatic screenshots on test failure (configured in `.env`)
- Playwright trace files for debugging (`.zip` format)
- Console logs and HTTP requests

## 🔐 Security & Best Practices

### Secrets Management
- ✅ No hardcoded credentials
- ✅ Environment variables via `.env`
- ✅ `.env` in `.gitignore`
- ✅ Example `.env.example` provided

### Data Privacy
- ✅ Test data cleaned up after execution
- ✅ Tenant isolation verified in all tests
- ✅ No production data in test data fixtures

### Code Quality
- ✅ PEP8 compliance
- ✅ Type hints where applicable
- ✅ Comprehensive logging
- ✅ Exception handling and recovery
- ✅ DRY principle maintained
- ✅ SOLID principles followed

## 🤖 CI/CD Integration

### GitHub Actions Workflow

Automated testing on:
- Push to `main` branch
- Pull requests
- Scheduled daily runs

Run matrix:
- Python 3.11, 3.12
- Chromium, Firefox, WebKit
- Multiple OS (Ubuntu, macOS, Windows)

See `.github/workflows/ci.yml` for full configuration.

## 📚 Documentation

- **[Test_Plan.md](docs/Test_Plan.md)** - Detailed test coverage matrix
- **[Framework_Design.md](docs/Framework_Design.md)** - Architecture and design patterns
- **[Assumptions.md](docs/Assumptions.md)** - Implementation assumptions and decisions
- **[FLAKY_TEST_ANALYSIS.md](docs/FLAKY_TEST_ANALYSIS.md)** - Part 1: Flaky test analysis

## 🐛 Troubleshooting

### Tests timing out
- Increase wait timeout in `config/environments.py`
- Check network connectivity
- Verify application is running

### Element not found errors
- Check element selectors in page objects
- Verify application structure hasn't changed
- Enable trace files for debugging

### Authentication failures
- Verify credentials in `.env`
- Check 2FA isn't blocking the account
- Verify API token hasn't expired

### Mobile test issues
- Verify BrowserStack configuration
- Check device name format in `config/browsers.py`
- Review device support matrix

## 🤝 Contributing

1. Create a feature branch
2. Follow existing code patterns
3. Add tests for new features
4. Update documentation
5. Create pull request

## 📝 License

This project is proprietary and confidential.

## 📞 Support

For issues or questions:
1. Check documentation in `docs/`
2. Review existing test examples
3. Enable trace files for debugging
4. Check GitHub Issues

---

**Last Updated:** July 2024
**Framework Version:** 1.0.0
**Python Version:** 3.11+
