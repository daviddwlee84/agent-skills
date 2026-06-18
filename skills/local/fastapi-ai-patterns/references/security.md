# Authentication, authorization, and API security

Read this when adding auth or hardening an endpoint. Covers the book's Chapter 6 in
original wording.

## Table of contents

1. [Authentication vs authorization](#authn-vs-authz)
2. [Password hashing](#password-hashing)
3. [JWT access tokens](#jwt-access-tokens)
4. [API keys, CORS, rate limiting](#api-keys-cors-rate-limiting)
5. [OWASP API risks — where breaches happen](#owasp-api-risks)
6. [Gotchas](#gotchas)

---

## Authn vs authz

- **Authentication** — who are you? (verify credentials, issue a token)
- **Authorization** — what may you do? (check permissions on each request)

They fail differently: 401 (unauthenticated) vs 403 (authenticated but not
permitted). The most damaging API bugs are authorization bugs, not authentication
bugs — see OWASP risks below.

## Password hashing

Hash with **bcrypt** or **argon2**, never a fast hash like SHA-256. Fast hashes
let an attacker try billions of guesses per second against a stolen table;
bcrypt/argon2 are deliberately slow and salted. Keep the cost factor high enough
that a single hash takes tens of milliseconds, and revisit it as hardware improves.
Never store or log plaintext passwords; never return the hash in any response.

## JWT access tokens

A JWT carries signed claims so the server can authenticate statelessly. The
standard pattern: a `/login` endpoint verifies credentials and returns a short-
lived access token; a `get_current_user` dependency validates the token on each
request and yields the user.

Critical rules:

- **Pin the verification algorithm.** Specify the expected algorithm explicitly
  when verifying; do not trust the token's own `alg` header. Accepting it enables
  the `alg=none` attack (a forged token claiming "no signature") and key-confusion
  attacks (RS256 verified as HS256 using the public key as the HMAC secret).
- **Keep access tokens short-lived.** Stateless JWTs can't be un-issued, so a
  leaked token is valid until expiry. For revocation, either keep tokens short and
  use refresh tokens, or maintain a denylist of revoked token IDs (`jti`) in Redis
  — which reintroduces state, the trade-off to weigh.
- **Token storage in browsers.** `localStorage` is readable by any XSS-injected
  script; `httpOnly` cookies aren't, but bring CSRF exposure (mitigate with
  SameSite + CSRF tokens). Neither is strictly "more secure" — they move the risk.

## API keys, CORS, rate limiting

- **API keys** suit server-to-server and machine clients where OAuth2/JWT is
  overkill. Treat them as secrets: hash them at rest, support rotation, scope them,
  and never log them.
- **CORS is not access control.** It's a browser policy telling browsers which
  origins may read responses from your API. It does nothing against non-browser
  clients (curl, servers) and must never be your authorization mechanism. Don't
  reflexively set `allow_origins=["*"]` with credentials.
- **Rate limiting** belongs at the gateway for coarse protection and/or a
  dependency/middleware for per-user limits. Redis gives a shared counter across
  workers/pods (in-process counters don't coordinate). Return 429 with `Retry-After`.

## OWASP API risks

The top API risk is **BOLA / IDOR** (broken object-level authorization): an
endpoint trusts a client-supplied object id without checking the caller owns it,
so `GET /invoices/{id}` leaks other tenants' invoices. Make it **structurally
impossible**, not reviewer-dependent:

- Filter every object fetch by owner/tenant in the query
  (`WHERE id = :id AND owner_id = :current_user_id`), so an unauthorized id returns
  404 by construction.
- For RAG/AI, apply the same rule to retrieval: filter chunks by the caller's ACL
  in the database query, never by instructing the model (see `ai-ml-serving.md`).

Other recurring risks: broken function-level authz (admin routes reachable by
non-admins), excessive data exposure (returning more than the client needs — fix
with response models), and unrestricted resource consumption (no rate/size limits).

## Gotchas

- **Not pinning the JWT algorithm enables `alg=none` and key-confusion forgeries.**
  Always pass the explicit expected algorithm to the verifier.
- **A login that distinguishes "email not found" from "wrong password" leaks
  account existence.** Return one generic 401 for both; also watch timing and
  signup/reset flows for the same leak.
- **CORS misunderstood as authorization** leaves the API open to every non-browser
  client. Authorization is a server-side check on every request.
- **In-process rate limiters don't coordinate across workers/pods** — a "100/min"
  limit becomes "100/min × N workers". Use a shared store (Redis).
- **A leaked JWT secret means every existing token is forgeable.** Rotate the
  secret (invalidating all tokens), force re-login, and audit access — don't just
  delete the repo commit.
