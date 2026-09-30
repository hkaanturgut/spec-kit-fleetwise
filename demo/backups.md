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

## Recording the checkpoints (dry run)

```bash
scripts/reset.sh
# run each step from docs/demo-guide.md, then after each one:
git add -A && git commit -m "<step>" && git tag -f <tag> && git push -f origin <tag>
```
