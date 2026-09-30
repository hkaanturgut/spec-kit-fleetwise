# Backup plan

The checkpoint tags already exist (recorded dry run). Record the video clips during your own rehearsal.

Record each clip during the final dry run and add the links here.

| Moment | Clip | Checkpoint |
| --- | --- | --- |
| Hook: vibe coding drift | _link_ | `s1-00-start` |
| Constitution from the code | _link_ | `s1-02-constitution` |
| Analyze catches the tenant gap | _link_ | `s1-05-plan-tasks` |
| Implement + converge, tests green | _link_ | `s1-06-implement` |
| Workflow run after a spec change | _link_ | `s1-07-workflow` |

## Record a rehearsal without moving checkpoints

Use the [single-page runbook](../README.md#presentation-and-live-demo-runbook)
in a dedicated practice clone. Reset discards local work; save anything needed first.

```bash
scripts/reset.sh
git switch -c "rehearsal-$(date +%Y%m%d-%H%M%S)"
```

Record each segment, save reviewed changes on the rehearsal branch, and add clip
links to the table above. Use the existing tags for recovery only.
Do not recreate or force-push the published `s1-*` tags.
