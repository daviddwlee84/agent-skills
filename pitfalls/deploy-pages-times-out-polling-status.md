# `actions/deploy-pages` hangs polling for deployment status and times out

## Symptom

A `Docs` workflow that normally finishes in ~30 seconds instead runs for
10 minutes and fails at the deploy step:

```
Run actions/deploy-pages@v5
Getting Pages deployment status...
Current status:
Getting Pages deployment status...
Current status:
...
(repeats for 10 minutes)
##[error]Timeout reached, aborting!
Canceling Pages deployment...
Canceled deployment with ID <sha>
```

Key signal: `Current status:` is followed by **nothing** — the Pages
API is returning an empty status string, not a real state like
`in_progress` / `succeed`. The `build` job itself succeeded and the
artifact uploaded fine; only `deploy-pages` is stuck.

`gh api repos/<owner>/<repo>/pages` afterwards shows `"status": null`
because the stuck deployment got canceled.

## Root cause

GitHub Pages backend transient failure. The deploy action polls
`/pages/deployment/status` until it sees a terminal state; when the
Pages service is degraded, the endpoint returns an empty body and the
poll loop just burns through the 10-minute default timeout.

Nothing in the repo configuration causes this. Adjacent commits on
the same workflow build + deploy cleanly in ~30 seconds both before
and after the incident.

## Workaround

Rerun the failed job:

```bash
gh run rerun <run-id> --failed
```

If reruns also hit the same timeout, check:

- [GitHub Status](https://www.githubstatus.com/) for an active Pages
  incident
- `gh api repos/<owner>/<repo>/pages` — if `status` is `null` and
  `build_type` / `source` still look correct, the repo config is fine
  and it really is a service-side problem

There is no repo-side fix. Do **not** start tweaking `mkdocs.yml`,
`permissions:`, or the `deploy-pages` version in response to this
symptom — the inputs were identical to prior green runs.

## Prevention

- Keep `Docs` workflow fast (current: ~30s build) so a legitimate
  stuck deploy is visually obvious next to prior run durations.
- Do not add retry logic to the workflow itself — `deploy-pages`
  already has internal polling; wrapping it in `continue-on-error` or
  a matrix-retry would mask real deploy failures.
- When a run fails unexpectedly, check build duration first. Sub-60s
  failure = real problem in our YAML or content. Multi-minute failure
  stuck in `Current status:` polling = infra; rerun.

## Where this was hit

Run
[`24846500693`](https://github.com/daviddwlee84/agent-skills/actions/runs/24846500693)
on commit `72647b7` ("Split Skills nav into Local vs Vendored"). The
immediately-prior run on `77c12c8` and the rerun of `72647b7` itself
both completed normally in ~30 seconds with the same workflow and
content pipeline.
