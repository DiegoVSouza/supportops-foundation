# Verification

Cause confirmed on the first attempt, 2026-10-30. Command: `python artifacts/evidence/git-128-diagnostic-043/reproduce.py`, cwd `projects/p00`, exit 0. Output: `artifacts/evidence/git-128-diagnostic-043/result.json`.

`git add` fails with `error: unable to write file .git/objects/7d/4290...: Filename too long`. The repository path is 219 characters, so the loose object path crosses the Windows 260-character limit. Git for Windows leaves `core.longpaths` off here.

| Case | Repo path length | `git add` exit |
| --- | --- | --- |
| phase040 layout with `.git` in the path | 219 | 128 |
| same length without `.git` | 219 | 128 |
| short path with `.git` | 105 | 0 |
| short path plain | 100 | 0 |

The `.git` component is irrelevant; length alone decides. This explains why phase042's short scratch path passed all 161 tests. It is an environment limit of the gate layout, not a product or test defect, so no source changed. The gate of phase040 stays consumed/FAIL and was not replayed.
