# Chapter 6 — Authentication, authorization, and API security

Read this when prepping auth, JWT, and OWASP API risks. Questions are original;
topics follow the book.

### Q1. Why must JWT verification pin the algorithm, and what is the `alg=none` attack?

A JWT's header declares its `alg`; if the verifier trusts that header, an attacker
sets `alg=none` (or swaps RS256→HS256 to use the public key as an HMAC secret) and
forges tokens. Always pass an explicit algorithm allowlist to the decoder so only
your expected algorithm is accepted.

### Q2. Design a revocation story for stateless JWTs and walk the trade-offs.

Stateless JWTs can't be un-issued, so options are: keep access tokens short-lived
with refresh tokens (small revocation window, mostly stateless), or maintain a
denylist of revoked `jti`s in Redis (immediate revocation but reintroduces state and
a lookup per request). The trade is revocation latency vs statelessness; most teams
combine short TTLs with a denylist for emergencies.

### Q3. What is BOLA, why does it top the OWASP API list, and how do you make it structurally impossible?

BOLA (broken object-level authorization / IDOR) is trusting a client-supplied object
id without checking ownership, so `GET /invoices/{id}` leaks other tenants' data.
It's #1 because it's easy to introduce and invisible in a happy-path review. Make it
structural by filtering every object fetch by owner/tenant in the query
(`WHERE id = :id AND owner_id = :uid`), so an unauthorized id returns 404 by
construction — not reviewer-dependent.

### Q4. Compare storing web-client tokens in `localStorage` vs `httpOnly` cookies, including CSRF.

`localStorage` is readable by any injected script, so it's exposed to XSS, but it's
immune to CSRF (the app attaches the token explicitly). `httpOnly` cookies are
invisible to JS (XSS-resistant) but are sent automatically, opening CSRF — mitigate
with SameSite and CSRF tokens. Neither is strictly safer; they move the risk between
XSS and CSRF.

### Q5. Why bcrypt/argon2 instead of SHA-256 for passwords, and how do you choose/maintain cost?

SHA-256 is fast, so a stolen table is cracked at billions of guesses/second. bcrypt
and argon2 are deliberately slow and salted, making brute force expensive. Choose a
cost factor so a single hash takes tens of milliseconds on your hardware, and revisit
it periodically (and on hardware upgrades), optionally rehashing on login.

### Q6. A login returns "email not found" vs "wrong password." What's wrong, and what else leaks existence?

It leaks which emails have accounts (an enumeration oracle). Return one generic
message for both. Other leaks: differing response timing (use constant-time
comparison and uniform work), and signup/password-reset flows that respond
differently for existing vs unknown emails.

### Q7. What does CORS actually protect, and why is it not access control?

CORS is a browser policy telling browsers which origins may read responses from your
API; it protects users' browsers from cross-origin reads. It does nothing against
non-browser clients (curl, servers), so it can't authorize anything — authorization
must be a server-side check on every request regardless of origin.

### Q8. Where should rate limiting live — gateway, middleware, or dependency — and what does Redis add?

Coarse, cheap limiting belongs at the gateway; per-user/per-route limits belong in a
dependency or middleware where you know the identity. Redis provides a shared counter
across workers and pods, so a "100/min" limit is actually 100/min globally rather
than 100/min × N in-process counters.

### Q9. Your JWT secret leaked in a public repo. Walk through the incident response.

Rotate the signing secret immediately (this invalidates all existing tokens) and
force re-authentication; audit access logs for suspicious activity during the
exposure window; purge the secret from git history and move it to a secret manager;
add secret scanning / pre-commit hooks to prevent recurrence. Deleting the commit
alone is insufficient — assume every prior token is forgeable.

### Q10. When do API keys beat OAuth2/JWT, and what hygiene do they require?

API keys suit server-to-server and machine clients where there's no human/OAuth flow
and long-lived credentials are acceptable. Hygiene: hash them at rest, scope them to
least privilege, support rotation and revocation, never log them, and prefer
per-client keys so one leak is contained.
