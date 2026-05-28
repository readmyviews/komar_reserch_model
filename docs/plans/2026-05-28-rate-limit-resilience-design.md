# Design Document: Gemini API Rate Limit (429) Resilience Overhaul

## Goal
Implement a robust, production-grade exponential backoff retry loop with randomized jitter and a multi-tiered model fallback chain to completely shield the Streamlit application from Gemini API rate limit (429 Quota Exceeded) errors.

## Proposed System Design

### 1. Multi-Tiered Fallback Chain
We will define an ordered fallback chain of models to try. If a model exhausts all of its retry attempts, the client will automatically move to the next model in the chain.

The chain is resolved dynamically based on the user's primary model configuration:
- If `primary_model == "gemini-2.5-flash"`:
  - Chain: `["gemini-2.5-flash", "gemini-2.0-flash"]`
- If `primary_model` is a custom/high-reasoning model (e.g. `gemini-2.5-pro`):
  - Chain: `[primary_model, "gemini-2.5-flash", "gemini-2.0-flash"]`

*Note: `gemini-2.0-flash` uses a separate quota pool from `gemini-2.5-flash`, providing independent resource limits if one is entirely saturated.*

### 2. Exponential Backoff with Randomized Jitter
To prevent thundering herd problems and ensure transient spikes clear, each model's retries will use exponential backoff:
$$\text{delay} = \text{base\_delay}^{\text{attempt}} + \text{jitter}$$
- `max_retries = 5` attempts per model in the chain.
- `base_delay = 2.0` seconds.
- `jitter = random.uniform(0.1, 1.0)` seconds.
- Sleep times will progress roughly as:
  - Attempt 1: ~2.5 seconds
  - Attempt 2: ~4.5 seconds
  - Attempt 3: ~8.5 seconds
  - Attempt 4: ~16.5 seconds
  - Attempt 5: Exhausted (moves to next model in chain)

### 3. Error Handling Flow
If a rate limit error (`429`, `RESOURCE_EXHAUSTED`, `quota exceeded`) is detected:
1. Log a warning with the current attempt number, model name, and calculated sleep delay.
2. Sleep for the calculated delay using `time.sleep()`.
3. Retry the request.
4. If all retries for the current model are exhausted, catch the exception, log a transition warning, and try the next model in the fallback chain.
5. If the entire fallback chain is completely exhausted, raise the final exception to `app.py` for user feedback.

### 4. Verification Plan
- **Mock Unit Tests**: Align `tests/test_agent.py` to simulate the full fallback chain:
  - Mock three consecutive rate limit failures on a primary custom model.
  - Verify it retries 5 times on the primary model, falls back to `gemini-2.5-flash`, retries there, and falls back to `gemini-2.0-flash`.
  - Patch `time.sleep` and `random.uniform` to ensure tests execute instantly.
- **Manual Verification**: Run Streamlit and query stocks to ensure live API calls execute flawlessly.
