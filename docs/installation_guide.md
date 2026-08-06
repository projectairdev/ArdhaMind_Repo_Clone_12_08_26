# Installation Guide

This guide provides step-by-step instructions for installing and deploying the **NIFTY Option Finder & Market Intelligence Workstation** on a completely clean machine.

---

## 📋 System Prerequisites

Ensure your machine meets the following baseline criteria:
- **Operating System**: Linux (Ubuntu 22.04 LTS or newer recommended), macOS, or Windows (via WSL2).
- **Python**: Version `3.11` or higher.
- **NodeJS**: Version `18.0.0` or higher (only required if serving the visual browser dashboard).
- **Internet Access**: Required to download dependencies and connect to optional API services (Google Gemini or Broker feeds).

---

## 🛠️ Step-by-Step Installation Flow

### Step 1: Clone or Extract the Repository
Extract the workstation files or clone the workspace into your desired directory:
```bash
mkdir -p /opt/trading_workstation
cd /opt/trading_workstation
# Extract package or clone
```

### Step 2: Establish the Python Virtual Environment
We recommend utilizing a isolated virtual environment to avoid package conflicts:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

### Step 3: Install Python Backend Dependencies
Install the required system and analytical packages via `pip`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Install NodeJS Frontend Dependencies
If you plan to view the React browser workspace UI, initialize the node modules:
```bash
npm install
```

### Step 5: Establish the Directory Structure
The workstation expects specific directories for operations tracking, logs, and caches. Ensure they exist:
```bash
mkdir -p logs cache
```

---

## ⚙️ Environment Variables Configuration

The workstation utilizes a `.env` file located at the root directory to authenticate with external services.

1. Copy the example environment template:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` to specify your actual API keys:
   ```env
   # Google Gemini API Key - Required for the AI Explanation Layer
   GEMINI_API_KEY="AIzaSyYourActualKeyHere..."

   # Manual Broker Integration Credentials (Kite Connect)
   KITE_API_KEY="your_kite_api_key"
   KITE_API_SECRET="your_kite_api_secret"
   KITE_ACCESS_TOKEN="your_kite_access_token_if_cached"
   ```

---

## 🏎️ Verification and Startup

### Running Diagnostic Verification
Before starting the system, execute the complete test suite to verify module integrity:
```bash
python3 -m unittest discover tests
```
*Expected Output: `Ran 183 tests... OK`*

### Starting the Workstation
- To start the workstation loop in the terminal:
  ```bash
  python3 -m src.pipeline.market_pipeline
  ```
- To start the developer server for the React browser dashboard:
  ```bash
  npm run dev
  ```

---

## 📋 Production Deployment Checklist

Before moving the workstation into active paper trading evaluation, verify each checkbox:

- [ ] **Python Version**: Verified `python3 --version` is >= 3.11.
- [ ] **Python Packages**: Run `python3 -c "import yaml; import psutil"` to confirm dependencies resolve.
- [ ] **Write Permissions**: Verified current user has read/write permissions on `/opt/trading_workstation/logs/` and `/opt/trading_workstation/cache/`.
- [ ] **Keys Configured**: `GEMINI_API_KEY` and Kite credentials exist in `.env`.
- [ ] **System Readiness**: Run the operations diagnostic script (Operations health panel) and verify overall readiness is `READY` or `READY_WITH_WARNINGS`.
- [ ] **Linter Status**: TypeScript linter (`npm run lint`) returns no errors.
