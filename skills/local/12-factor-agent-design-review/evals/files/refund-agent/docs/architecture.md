# Refund agent architecture

The HTTP controller calls `runRefundAgent` and returns its final reply.

The agent currently serves the web support UI only. Slack and email adapters are
planned for a later release.

Refunds above USD 500 should eventually require manager approval. Approval UI,
callback authentication, timeout handling, and worker restart behavior are not
defined yet.

Application logs record request IDs, but the fixture does not include logging or
observability configuration.
