# renovate-config

The tj-agents organization's shared Renovate configuration. `default.json` is the preset Renovate applies to
every repository in the organization; `org-inherited-config.json` is the org-level default config that makes
that inheritance automatic, with onboarding off and a repository's own `renovate.json` optional.

## How it fits

TJ Agents keeps every cross-repository dependency as a pinned, versioned reference rather than a path-loaded
or vendored copy. Renovate is what keeps those pins current: it opens the bump PR, and the PR auto-merges once
the consumer's CI passes. This repository is the one place that behavior is configured, so no other repository
needs to carry its own Renovate setup. The GitHub App is installed only on the `tj-agents` organization, so
employer organizations are never reachable by it.

## Status

Org-level inheritance is live: a repository without its own Renovate config gets this preset automatically.

## Configuration

- `org-inherited-config.json`: the org default config (`onboarding: false`, `requireConfig: "optional"`,
  extending this repository's preset). This is what makes inheritance automatic.
- `default.json`: the actual preset — squash auto-merge on green CI, non-major dependencies grouped, a
  nightly schedule, and an explicit carve-out that disables bumping the `tj-agents/template` GitHub Action
  (Template is consumed through its own generator/update path, not a dependency bump).

A repository only needs its own `renovate.json` to add something genuinely specific to it, such as a custom
manager; it should otherwise rely on inheritance. The inherited config does not reach a repository that has its
own config file, so that file must extend `github>tj-agents/renovate-config`, or its Renovate PRs lose automerge
and wait for a human. The `automerge` workflow fails daily and on every change here when any repository's own
config omits the preset or disables automerge.
