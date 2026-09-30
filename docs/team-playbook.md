# Team playbook: Spec Kit with many developers

In a team, the spec is the contract between people, not just between one developer and an AI. This is a recommended operating model built on Spec Kit's mechanics; Spec Kit does not enforce it by itself.

**Golden rule:** one feature = one `specs/<feature>/` folder = one branch = reviewed through pull requests.

## Three review gates under one constitution

```mermaid
flowchart LR
    K["Constitution<br/>changed only via PR + CODEOWNERS"]
    K -. checked at every step .-> S
    K -. checked at every step .-> P
    K -. checked at every step .-> B

    S["1. Spec<br/>specify + clarify<br/>owner: product + dev"] --> G1{"Gate 1<br/>spec PR"}
    G1 -- approved --> P["2. Plan<br/>plan, tasks, analyze<br/>owner: tech lead"]
    P --> G2{"Gate 2<br/>plan PR"}
    G2 -- approved --> B["3. Build<br/>issues to devs + coding agent<br/>implement, converge"]
    B --> G3{"Gate 3<br/>code PRs vs spec"}
    G3 -- merged --> M["main: spec and code<br/>ship together"]
    M -. "requirement change:<br/>edit the spec first" .-> S
```

## Who owns what

| Role | Owns | Spec Kit steps |
| --- | --- | --- |
| Product owner / BA | The what and why | `specify`, `clarify`, reviews the requirements checklist |
| Tech lead / architect | The how, plus the rules | Constitution owner (CODEOWNERS), `plan`, `analyze` gate |
| Developers | Delivery | `tasks`, `implement`, `converge`, code PRs |
| Copilot coding agent | Parallel, well-scoped tasks | Picks up task issues, opens PRs for human review |
| Platform / DevEx | Consistency across repos | Pinned Spec Kit version, shared presets, shared workflows, baseline constitution |

## One feature through the team

```mermaid
sequenceDiagram
    autonumber
    actor PO as Product owner
    actor TL as Tech lead
    actor Dev as Developer
    participant GH as GitHub
    participant CA as Copilot coding agent

    PO->>Dev: Feature idea
    Dev->>GH: Branch + /speckit-specify, /speckit-clarify
    Dev->>GH: Spec PR (spec.md, checklist)
    PO->>GH: Approve intent
    TL->>GH: Approve intent (Gate 1)
    Dev->>GH: /speckit-plan, /speckit-tasks, /speckit-analyze
    TL->>GH: Approve plan PR (Gate 2)
    Dev->>GH: /speckit-taskstoissues
    GH->>CA: Independent [P] tasks assigned
    CA->>GH: Task PRs
    Dev->>GH: Dependent tasks, /speckit-converge
    TL->>GH: Review code PRs against spec (Gate 3)
    GH-->>PO: Merged: spec and code ship together
```

## Parallel work without collisions

```mermaid
flowchart TB
    subgraph Main["main"]
        C["constitution.md<br/>(rarely changes)"]
    end
    subgraph A["branch: feature A"]
        A1["specs/20261001-093000-dispatcher/"]
    end
    subgraph B["branch: feature B"]
        B1["specs/20261001-101500-parts-alerts/"]
    end
    Main --> A
    Main --> B
    A1 --> MA["merge A"]
    B1 --> MB["merge B"]
    MA --> R["No conflicts: each feature<br/>lives in its own folder"]
    MB --> R
```

## Pitfalls and fixes

| Pitfall | Fix |
| --- | --- |
| Two developers create `003-...` on separate branches | Switch the git extension to `branch_numbering: timestamp` (YYYYMMDD-HHMMSS prefixes), or prefix names with the issue number |
| The "active feature" is wrong after switching branches | Spec Kit tracks it in `.specify/feature.json`, which is gitignored per machine. Point it at your feature, or set `SPECIFY_FEATURE_DIRECTORY` |
| Spec and code drift apart | Team rule: a requirement change starts with a spec edit PR, never a code-only PR |
| Constitution edited casually | Protect `.specify/memory/constitution.md` with CODEOWNERS |
| Each repo invents its own process | The platform team ships a shared preset, a shared workflow, and a baseline constitution; teams add only local rules (workflow overlays) |

Example `CODEOWNERS`:

```text
/.specify/memory/constitution.md   @your-org/tech-leads
/workflows/                        @your-org/platform
```
