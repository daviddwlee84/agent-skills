# sed: RE error: illegal byte sequence in a SpecStory transcript

## Symptom

`agent-commit-metadata.sh` fails with:

```text
sed: RE error: illegal byte sequence
```

## Root cause

A recorded tool-input fragment contained a malformed UTF-8 byte. Both the staged
snapshot and the live file failed strict UTF-8 decoding at the same interior
offset, so this was existing archive corruption rather than a partial final line.
macOS sed rejects the data under a UTF-8 locale.

## Workaround

Validate the selected staged blob with strict UTF-8 decoding. For the commit
snapshot, preserve invalid bytes as visible ASCII escapes (Python's
`errors='backslashreplace'`), then stage that normalized blob and rerun the secret
scan. Leave a recorder's live file untouched. Generate provenance from the final
staged blob, never from a newer live generation.

`LC_ALL=C` permits ASCII metadata matching, but by itself does not repair the
archive encoding. Do not mistake a successful metadata command for valid UTF-8.

## Prevention

Truncate recorded tool text on character boundaries and validate encoded output
before publishing a transcript. Keep any archive normalization scoped to exact
files and a stable snapshot; never run a formatter over a live recording tree.
