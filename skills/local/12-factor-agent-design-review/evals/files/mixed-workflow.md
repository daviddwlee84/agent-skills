# Current claims-triage workflow

Incoming claims arrive through a web form. The controller passes the form text
directly to a LangGraph agent and waits for the graph to finish.

The graph uses framework-default message state and a prompt embedded in the
graph node. Prompt changes are deployed with application code, but prompt
versions are not recorded with runs.

The model may call `lookup_policy`, `request_manager_approval`, or `approve_claim`.
Tool arguments are validated by provider function calling. The graph invokes
the corresponding Python function after validation.

`request_manager_approval` sends a Slack message, then the worker polls Slack in
the same process until a response arrives. Graph checkpoints use the in-memory
development saver. A process restart loses the pending run.

Tool exceptions are appended to the framework message list and retried until
the graph reaches an end node. There is no documented retry budget or escalation
policy.

The team wants to retain LangGraph routing and visualization, add asynchronous
manager approval, survive restarts and duplicate Slack callbacks, bound repeated
tool failures, and reproduce the exact input presented to the model.
