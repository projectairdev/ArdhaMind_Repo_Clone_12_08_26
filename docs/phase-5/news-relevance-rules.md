# nifty relevance and impact assessment rules

All market impact evaluations are performed deterministically without the use of OpenAI or other LLM APIs.

## 1. NIFTY Constituent Weight Metadata (Version 1.0.0)

Versioned stock weightings are configured inside [impact_assessor.py](file:///e:/AIR/ArdhaMind01/src/news_engine/impact_assessor.py):

| Ticker Ticker | Sector | Weight (%) |
|---|---|---|
| `RELIANCE` | Energy | 9.8% |
| `HDFCBANK` | Banking | 11.5% |
| `ICICIBANK` | Banking | 7.8% |
| `INFY` | Technology | 5.2% |
| `TCS` | Technology | 4.1% |
| `ITC` | Consumer Goods | 4.5% |
| `LT` | Construction | 3.8% |
| `SBIN` | Banking | 3.2% |
| `BHARTIARTL` | Telecom | 3.0% |
| `KOTAKBANK` | Banking | 2.7% |

*If verified weights are unavailable, index-wide weighted calculations are skipped.*

---

## 2. NIFTY Relevance Score (0.0 to 10.0 scale)

The score is calculated accumulatively based on:
1. **Constituent Ticker Mention**: `+4.0` if any NIFTY constituent symbol is mentioned in the headline/description.
2. **Heavyweight Weighting**: `+3.0` if the highest-weight mentioned constituent exceeds 5.0% index weighting.
3. **Category Modifier**: `+5.0` if category is central bank (`RBI`), regulatory (`SEBI`), or exchange policies (`NSE/BSE`).
4. **Source Type Modifier**: `+3.0` if it originates from an official source.

*Relevance score is capped at `10.0` maximum and defaults to `1.0` minimum.*

---

## 3. Direction and Sentiment Heuristics

Expected directions include:
- `positive`
- `negative`
- `mixed`
- `uncertain`
- `not_assessed`

### Sentiment Lexicons
- **Positive Keywords**: `jump`, `surge`, `growth`, `cut`, `cuts`, `positive`, `buying`, `rally`, `profit`, `cools`, `ease`, `record high`, `beat`, `higher`, `approval`, `dividend`.
- **Negative Keywords**: `fall`, `drop`, `slump`, `down`, `crash`, `war`, `missile`, `drone`, `tension`, `sanction`, `selling`, `hike`, `hikes`, `sticky`, `hot`, `deficit`, `selloff`, `penalty`, `loss`, `losses`.

### Context-Aware Modifiers
- **Oil Price**: If `oil` or `crude` is found, a rise in oil is treated as a negative match, and a drop in oil is treated as a positive match.
- **Inflation**: If `inflation` is found, rising/sticky inflation is treated as a negative match, and cooling/softening inflation is treated as a positive match.

### Direction Assignment
- **Mixed**: Both positive and negative keywords match. Confidence = `0.40`.
- **Positive**: Only positive keywords match. Confidence = `0.80` (if >= 2 words) or `0.60` (if 1 word).
- **Negative**: Only negative keywords match. Confidence = `0.80` (if >= 2 words) or `0.60` (if 1 word).
- **Uncertain**: Matches exist but score is balanced/neutral. Confidence = `0.50`.
- **Not Assessed**: Zero keyword matches. Confidence = `0.0`.
