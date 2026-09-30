# Backup plan

The checkpoint tags already exist (recorded dry run). Record the video clips during your own rehearsal.

Record each clip during the final dry run and add the links here.

| Moment | Clip | Checkpoint |
| --- | --- | --- |
| Hook: vibe coding drift | _link_ | `s1-00-start` |
| Constitution from the code | _link_ | `s1-02-constitution` |
| Analyze catches the tenant gap | _link_ | `s1-05-plan-tasks` |
| Implement + converge, tests green | _link_ | `s1-06-implement` |
| Delivery workflow: review gates, task issues, implementation, draft PR | _link_ | Current `origin/main` plus initialization from `s1-02-constitution`, in a separate worktree |
| Optional advanced workflow after a spec change | _link_ | `s1-07-workflow` |

## Record a rehearsal without moving checkpoints

Use the [single-page runbook](../README.md#walkthrough-adopt-spec-kit-on-this-repo)
in a dedicated practice clone. Reset discards local work; save anything needed first.

```bash
scripts/reset.sh
git switch -c "rehearsal-$(date +%Y%m%d-%H%M%S)"
```

Record each segment, save reviewed changes on the rehearsal branch, and add clip
links to the table above. Use the existing tags for recovery only.
Do not recreate or force-push the published `s1-*` tags.

For the delivery workflow clip, use the README's separate-worktree preparation
instead of resetting the main demo. Capture the invocation, review prompts,
GitHub task issues, and automatic progression to implementation and a draft PR. Generated output need not
match a reference result. `s1-07-workflow` records the older custom workflow,
not a completed delivery run. Keep the issues/PR labeled `demo`; closing them
with `scripts/reset.sh --github` is an explicit cleanup action, not a pipeline step.
