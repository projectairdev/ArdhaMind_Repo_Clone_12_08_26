# Part 12: Verification & Testing Strategy

This section documents the testing philosophy, automated regression suite design, mocking strategies, and isolation rules within the NIFTY Option Finder & Market Intelligence Workstation.

---

## 🧪 Testing Philosophy

The workstation treats testing as a core design constraint, not an afterthought. In index option trading, a single calculation bug or out-of-order state transition can lead to significant financial loss.

We maintain a strict **100% Passing Test Mandate** for all pull requests.

Our verification suite is built on three core pillars:
1. **Deterministic Testing**: Given the same inputs, calculations must return identical results every time. No random variables are permitted inside calculation tests.
2. **Stateless Isolation**: Tests must run without reading live internet resources, databases, or writing to shared temp files. All external components are fully mocked.
3. **Execution Speed**: The full suite of 180+ tests must run in under 2 seconds, encouraging developers to execute tests frequently during development.

---

## 📂 Core Test Architecture

Tests are stored inside `/tests/` and mirror the structure of the `src/` modules:

```text
/tests/
├── options/                   # Options chain parsing & calculation tests
├── test_ai_explanation.py     # Mock prompt and response verification
├── test_broker_integration.py # Session token and connection mocks
├── test_confidence_engine.py  # Confidence score calculations
├── test_decision_engine.py    # Non-contradicting action state checks
├── test_historical_runner.py  # Replay simulation verification
├── test_news_intelligence.py  # Deduplication and sentiment decay checks
├── test_operations_manager.py # Diagnostic checks and readiness scores
├── test_risk_engine_v2.py     # Drawdown limits and sizing checks
└── test_trade_planner.py      # Entry, target, and stop calculations
```

---

## 🛡️ Mocking Strategies & Stateless Isolation

To isolate tests from external services, the workstation uses standard mocking patterns:

### 1. Mocking the Google Gemini API
To prevent testing dependencies on network availability and API key balances, the AI Explanation tests mock the underlying Google GenAI SDK:

```python
import unittest
from unittest.mock import MagicMock, patch
from src.explanation_engine.explanation import ExplanationEngine

class TestAIExplanation(unittest.TestCase):
    @patch('src.explanation_engine.explanation.GoogleGenAI')
    def test_explanation_generation(self, mock_gen_ai) -> None:
        # Arrange mock response
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "Mock explanation of strategy."
        mock_gen_ai.return_value = mock_client

        # Act
        engine = ExplanationEngine()
        result = engine.generate_explanation(mock_decision_report)

        # Assert
        self.assertIn("Mock", result)
```

### 2. Mocking File System IO
To prevent tests from creating or modifying live files on the developer's system, file loaders are mocked to read configuration schemas from local string constants:

```python
@patch('src.utils.io_utils.open_file')
def test_config_loader(self, mock_open) -> None:
    mock_open.return_value = '{"max_risk_score": 50.0, "max_capital_allocation": 100000}'
    config = self.loader.load("mock_path.json")
    self.assertEqual(config.max_risk_score, 50.0)
```

---

## 📈 Regression Verification Workflows

The workstation relies on automated regression testing to prevent breaking changes:

- **Local Pre-Commit Checks**: Developers run `python3 -m unittest discover tests` locally prior to staging code changes.
- **Continuous Integration (CI)**: When a PR is opened, the CI system runs the full test suite and executes the linter check (`npm run lint`). The PR cannot be merged unless all checks pass.

This rigorous, isolation-first testing structure ensures that the NIFTY Option Workstation remains fully functional and reliable as the codebase evolves.
