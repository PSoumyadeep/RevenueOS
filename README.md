# RevenueOS — Razorpay AI Buildathon Demo

Autonomous Revenue Recovery Agent for the AI Revenue Recovery track.

## Features
- Agentic loop: Observe → Retrieve → Reason → Plan → Guard → Act → Verify
- RAG over merchant policies, payment knowledge and historical cases
- Customer/payment context investigation
- Deterministic guardrails: confidence threshold, retry limits, high-value escalation
- Recovery actions: simulated retry or Razorpay Test Mode Payment Link
- Recovery cases + audit trail
- Evaluation framework with blind-retry/static-rule baselines
- Works offline in DEMO_MODE

## Run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Open http://localhost:8000.

## Live demo
1. At-Risk Payments → `pay_demo_001` → Investigate.
2. Show customer history, failure reason, retrieved policy, confidence and action.
3. Create Case & Execute.
4. Show recovered revenue.
5. Recovery Cases → Audit.
6. Evaluation → explain baseline methodology.

## Razorpay Test Mode
Set `DEMO_MODE=false`, `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `.env`. The recovery-link action then calls `POST /v1/payment_links` using Razorpay Test Mode credentials. Keep secrets out of Git.

Official docs:
https://razorpay.com/docs/api/
https://razorpay.com/docs/api/payments/payment-links/create-standard/
https://razorpay.com/docs/api/payments/
https://razorpay.com/docs/webhooks/

## Production hardening
- Replace TF-IDF with pgvector embeddings.
- Add a structured-output LLM planner; keep financial authority deterministic.
- Validate Razorpay webhook signatures and idempotency.
- Use a queue for asynchronous recovery jobs.
- Run a held-out 10k+ evaluation batch and report recovered revenue, recovery rate, unnecessary intervention, escalation rate and policy violations.
