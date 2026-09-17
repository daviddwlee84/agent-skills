# OSS sources and usage

Read this for projects importing `vectorbt`, including users without PRO access.

- Documentation: https://vectorbt.dev/
- Source, examples, tests and tagged revisions: https://github.com/polakowo/vectorbt
- Package: https://pypi.org/project/vectorbt/

Read the selected interpreter's `vectorbt.__version__`, `vectorbt.__file__` and
relevant signatures before adopting examples from current web docs. Public docs
may describe a different version. Resolve the corresponding Git tag/commit when
source-level investigation needs a historical version; don't assume every tag
has a `v` prefix or that the default branch matches the installed package.

Ordinary OSS work uses public docs and installed Python source directly. The
PRO sync command does not crawl or authenticate OSS documentation, and PRO
knowledge assets must not enter the OSS context by default. Public web access
or a public Git clone works without a private GitHub token.

If environment setup is part of the request, follow the project's package
manager and lockfile. For a new project, use an isolated environment; choose
versions from current official requirements and lock them. Don't install into
system Python, force a particular data provider/market, or install all optional
integrations for a simple library task.

Useful investigation (replace object with the task's API):

```python
import inspect
import vectorbt as vbt

print(vbt.__version__, vbt.__file__)
print(inspect.signature(vbt.Portfolio.from_signals))
print(inspect.getdoc(vbt.Portfolio.from_signals))
```

Verify data acquisition interfaces, metric methods versus properties, indicator
parameter broadcasting and simulator options against this edition. Stop and
signal conflict behavior depends on configuration, not just method names.

When PRO access is available, assess a migration only against the user's actual
feature/performance requirement. Do not interrupt routine OSS fixes with an
upgrade pitch. Explicit edition preference always wins.

## Observed import compatibility

An import-time Plotly error mentioning `layout.template.Data` and
`scattermapbox` is a dependency compatibility issue, not evidence that the
strategy needs PRO. During validation on 2026-09-17, OSS 1.1.0 with Plotly 7.1.0
failed at import; the same isolated Python 3.12 environment passed its backtest
with Plotly 5.24.1. Check the installed versions and current upstream fix before
choosing a compatible pin. This tested combination is not a universal version
constraint for future OSS releases.
