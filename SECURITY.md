# Security notes

## Secrets
- Never commit broker passwords, MT5 investor/master passwords, API tokens, private keys, or Streamlit secrets.
- Keep deployment credentials in Streamlit Community Cloud app secrets or the hosting provider's encrypted environment-variable store.
- The repository is currently public. Treat anything committed to it as public, including historical commits.
- If a credential was ever committed, remove it from active use and rotate/revoke it immediately. Deleting the line in a later commit does not make the old credential safe.

## Trading safety
- This application is currently an analysis dashboard. It does not connect to a broker or place orders.
- Do not add live order execution until authentication, authorization, risk limits, audit logging, and demo-account testing are implemented.
- Never paste broker passwords or one-time codes into chat or source files.

## Reporting
Do not publish vulnerabilities or credentials in public issues. Rotate exposed credentials first and report security concerns privately to the repository owner.
