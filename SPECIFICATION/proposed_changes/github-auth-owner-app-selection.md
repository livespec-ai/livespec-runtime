---
topic: github-auth-owner-app-selection
author: claude-opus-5-5
created_at: 2026-11-15T09:32:50Z
---

## Proposal: Select the GitHub App by the target repository's owner

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

load_github_app_config gains an optional `repository` argument and an optional GITHUB_APP_OWNER_MAP environment variable declaring, per GitHub owner, which environment variables hold that owner's App id and private key. When both are present the App is chosen by the repository's owner; an owner with no declared App fails closed naming the owner before any token request, and a malformed map or an entry naming absent variables fails closed naming them. Without the map, or without a repository, the single-App GITHUB_APP_ID / GITHUB_PRIVATE_KEY configuration resolves exactly as today, so a one-owner tenant needs no change. GithubAppConfig gains a `repository` field so mint can resolve the installation from it.

### Motivation

Work item livespec-runtime-wb7yco (option A, the durable fix for the host-side GitHub App mint gate of the livespec-ai org cutover). After the cutover the fleet is mixed: ten repositories are owned by livespec-ai (org App 5761962, installation 182016479) and the rest by thewoolleyman (personal App 3668528, installation 131208965). The current contract reads one fixed GITHUB_APP_ID / GITHUB_PRIVATE_KEY pair, so one process cannot mint for both owners. The interim option C hides the selection in per-repository credential_wrapper strings and fails for every process spanning both owners: fleet-wide sweeps, the adopter currency lane, and the reconcile and incident fleet commands. The orchestrator callers, the vendored copies in consumer repositories, the orchestrator-image entrypoint and the retirement of the option-C overrides are realization work in other repositories and are out of this spec target.

### Proposed Changes

Every existing H2 heading below is kept VERBATIM, so the existing `tests/heading-coverage.json` rows and the work-item references that cite them keep resolving. Only bodies change, and new H2 scenarios are added.

#### 1. `SPECIFICATION/contracts.md` §"`livespec_runtime.github_auth.config`" — replace the section body with:

- `GithubAppConfig` — frozen, slotted, kw-only dataclass:
  `app_id: str`, `private_key_pem: str`,
  `api_url: str = DEFAULT_API_URL`,
  `installation_id: str | None = None`,
  `repository: str | None = None`. `repository`, when set, is the
  target repository in `owner/name` form that the config was resolved
  for.
- `DEFAULT_API_URL` — `"https://api.github.com"`.
- `OWNER_MAP_VAR` — `"GITHUB_APP_OWNER_MAP"`.
- `load_github_app_config(*, environ: Mapping[str, str], repository:
  str | None = None) -> Result[GithubAppConfig, GithubAppAuthError]` —
  the env-only input boundary. Inputs come ONLY from environment
  variables injected by the consuming tenant's `credential_wrapper`,
  plus the caller-supplied `repository`. It is a total, process-free
  function of those inputs: it MUST NOT perform any network request.
  - **Owner-to-App map.** `GITHUB_APP_OWNER_MAP` (OPTIONAL) declares
    which GitHub App mints for which repository owner. Its value MUST
    be a JSON object whose keys are GitHub owner logins and whose
    values are objects carrying exactly the two string fields
    `app_id_var` and `private_key_var`, each NAMING the environment
    variable that holds that App's id and PEM private key. The map
    carries variable NAMES, never secret values. Example:
    `{"livespec-ai": {"app_id_var": "GITHUB_APP_ID_ORG",
    "private_key_var": "GITHUB_PRIVATE_KEY_ORG"}, "thewoolleyman":
    {"app_id_var": "GITHUB_APP_ID", "private_key_var":
    "GITHUB_PRIVATE_KEY"}}`.
  - **Selection by owner.** When `GITHUB_APP_OWNER_MAP` is set and
    non-empty AND `repository` is given, the App MUST be selected by
    the repository's owner (the segment before the `/`), matched
    against the map's keys case-insensitively, because GitHub logins
    are case-insensitive. The selected entry's `app_id_var` and
    `private_key_var` are then read from `environ`; both are REQUIRED
    and an empty string counts as missing. The resulting config MUST
    carry `repository` and MUST carry `installation_id = None`:
    `GITHUB_APP_INSTALLATION_ID` MUST NOT be applied to an
    owner-selected App, since one pin cannot be correct for two Apps;
    the installation is resolved from the repository at mint time.
  - **Undeclared owner fails closed.** When the map is in force and
    the repository's owner matches no key, resolution MUST put a
    `GithubAppAuthError` on the failure track whose detail names that
    owner, lists the declared owners, and points the operator at the
    tenant's `credential_wrapper`. It MUST NOT fall back to
    `GITHUB_APP_ID` / `GITHUB_PRIVATE_KEY` or to any other declared
    App, and because the boundary is network-free, no token request
    can have been made.
  - **Malformed map fails closed.** A `GITHUB_APP_OWNER_MAP` value
    that is not valid JSON, is not an object, or has an entry lacking
    a non-empty string `app_id_var` or `private_key_var` MUST put a
    `GithubAppAuthError` on the failure track naming
    `GITHUB_APP_OWNER_MAP` and the offending owner key where there is
    one. A map whose selected entry names absent-or-empty variables
    MUST fail closed naming EVERY such variable.
  - **Single-App configuration.** When `GITHUB_APP_OWNER_MAP` is
    absent or empty, OR when no `repository` is given, resolution
    reads `GITHUB_APP_ID` and `GITHUB_PRIVATE_KEY` (REQUIRED; an
    empty string counts as missing) and `GITHUB_APP_INSTALLATION_ID`
    (OPTIONAL installation pin), exactly as before. This single-App
    configuration MUST stay valid for a tenant whose repositories all
    have one owner, with or without a `repository`; when a
    `repository` is given it MUST be carried into the config.
  - `GITHUB_API_URL` (OPTIONAL API-root override, e.g. GitHub
    Enterprise) applies in both modes.
  - Any absent-or-empty required variable MUST put a
    `GithubAppAuthError` on the failure track naming EVERY missing
    variable and pointing the operator at the tenant's
    `credential_wrapper`; there MUST NOT be a fallback to any fleet
    credential.
  - A `repository` that is not exactly one non-empty owner segment
    and one non-empty name segment joined by a single `/` is a caller
    bug and MUST raise `ValueError` rather than land on the failure
    track.

#### 2. `SPECIFICATION/scenarios.md` — amend the existing scenario body

`## Scenario: load the App config from the tenant's credential-wrapper environment` becomes:

```
Given an environment mapping with GITHUB_APP_ID "12345" and GITHUB_PRIVATE_KEY set to a PEM
And no GITHUB_APP_INSTALLATION_ID, no GITHUB_API_URL and no GITHUB_APP_OWNER_MAP
When load_github_app_config is invoked with that environ and no repository
Then the result is a Success carrying a GithubAppConfig with app_id "12345" and that private_key_pem
And that config's api_url is DEFAULT_API_URL, "https://api.github.com"
And its installation_id is None
And its repository is None
```

#### 3. `SPECIFICATION/scenarios.md` — add these scenarios immediately after `## Scenario: the optional installation pin and API-root override are carried into the config`

```
## Scenario: an owner-to-App map selects the App by the target repository's owner

Given an environment mapping with GITHUB_APP_ID_ORG "5761962", GITHUB_PRIVATE_KEY_ORG set to the org PEM, GITHUB_APP_ID "3668528" and GITHUB_PRIVATE_KEY set to the personal PEM
And GITHUB_APP_OWNER_MAP mapping "livespec-ai" to app_id_var "GITHUB_APP_ID_ORG" and private_key_var "GITHUB_PRIVATE_KEY_ORG", and "thewoolleyman" to app_id_var "GITHUB_APP_ID" and private_key_var "GITHUB_PRIVATE_KEY"
And GITHUB_APP_INSTALLATION_ID "131208965"
When load_github_app_config is invoked with that environ and repository "livespec-ai/livespec"
Then the result is a Success carrying a GithubAppConfig with app_id "5761962", the org PEM and repository "livespec-ai/livespec"
And its installation_id is None, because the installation pin is not applied to an owner-selected App
And when it is invoked with the same environ and repository "thewoolleyman/livespec-runtime" the config carries app_id "3668528", the personal PEM and repository "thewoolleyman/livespec-runtime"
And when it is invoked with repository "LiveSpec-AI/livespec" the owner matches "livespec-ai" case-insensitively and the org App is selected

## Scenario: a single-App configuration stays valid for a tenant with one owner

Given an environment mapping with GITHUB_APP_ID "12345" and GITHUB_PRIVATE_KEY set to a PEM and no GITHUB_APP_OWNER_MAP
When load_github_app_config is invoked with that environ and repository "thewoolleyman/livespec-runtime"
Then the result is a Success carrying a GithubAppConfig with app_id "12345" and that private_key_pem
And its repository is "thewoolleyman/livespec-runtime"

## Scenario: a repository whose owner has no declared App fails closed naming the owner

Given an environment mapping whose GITHUB_APP_OWNER_MAP declares only "livespec-ai" and "thewoolleyman", with every variable both entries name set
And GITHUB_APP_ID and GITHUB_PRIVATE_KEY also set
When load_github_app_config is invoked with that environ and repository "someone-else/tool"
Then the result is a Failure carrying GithubAppAuthError
And the error's detail names the owner "someone-else" and lists the declared owners "livespec-ai" and "thewoolleyman"
And the error's detail points the operator at the consuming tenant's credential_wrapper
And neither GITHUB_APP_ID nor any declared App is used as a fallback
And no token request is made, because no config exists to mint with

## Scenario: an owner-to-App map entry naming absent variables fails closed naming them

Given an environment mapping whose GITHUB_APP_OWNER_MAP maps "livespec-ai" to app_id_var "GITHUB_APP_ID_ORG" and private_key_var "GITHUB_PRIVATE_KEY_ORG"
And GITHUB_APP_ID_ORG is the empty string and GITHUB_PRIVATE_KEY_ORG is absent
When load_github_app_config is invoked with that environ and repository "livespec-ai/livespec"
Then the result is a Failure carrying GithubAppAuthError
And the error's detail names BOTH GITHUB_APP_ID_ORG and GITHUB_PRIVATE_KEY_ORG as missing

## Scenario: a malformed owner-to-App map fails closed naming the variable

Given an environment mapping whose GITHUB_APP_OWNER_MAP is not a JSON object
When load_github_app_config is invoked with that environ and repository "livespec-ai/livespec"
Then the result is a Failure carrying GithubAppAuthError
And the error's detail names GITHUB_APP_OWNER_MAP
```

The revise that accepts this proposal MUST add one `tests/heading-coverage.json` row per new H2 in the same commit, per the revise co-edit discipline.

## Proposal: Resolve the installation from the target repository when it is known

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

mint_installation_token resolves the installation in a fixed order: the pinned installation_id; else, when the config carries a repository, GET /repos/{owner}/{repo}/installation; else the existing sole-installation discovery via GET /app/installations. A repository the App is not installed on fails closed naming the repository and App id with no token request. The three existing mint scenarios keep their headings and gain an explicit repository-is-None (or pin-wins) given, and three new scenarios cover the repository path, its failure, and one process minting for two owners.

### Motivation

Work item livespec-runtime-wb7yco. Today an unpinned mint lists the App's installations and refuses at two or more, so adding a second installation of either App breaks every mint of that App, and a single process-wide GITHUB_APP_INSTALLATION_ID pin cannot be right for two Apps. Asking GitHub which installation covers the target repository removes both failure modes whenever the repository is known, while the sole-installation discovery remains for callers that give no repository.

### Proposed Changes

#### 1. `SPECIFICATION/contracts.md` §"`livespec_runtime.github_auth.mint`" — replace the `mint_installation_token` bullet with:

- `mint_installation_token(*, config: GithubAppConfig, issued_at:
  int, seams: MintSeams = DEFAULT_MINT_SEAMS) ->
  IOResult[str, GithubAppAuthError]` — mint on demand: sign the App
  JWT, resolve the installation, then
  `POST /app/installations/{id}/access_tokens`. The installation MUST
  be resolved in this order:
  1. the pinned `installation_id` when the config carries one — no
     discovery request is made;
  2. else, when the config carries a `repository` `owner/name`,
     `GET /repos/{owner}/{name}/installation`, using the `id` of the
     returned installation. A failure of that request (including the
     404 GitHub returns when the App is not installed on the
     repository) or a response with no `id` is an EXPECTED failure
     that MUST land on the failure track as `GithubAppAuthError`
     naming the repository and the App id, and no access token MAY be
     requested. `GET /app/installations` MUST NOT be requested on this
     path;
  3. else (no pin and no repository) sole-installation discovery via
     `GET /app/installations` — any installation count other than one
     is an EXPECTED ambiguity that MUST land on the failure track as
     `GithubAppAuthError` directing the operator to pin
     `GITHUB_APP_INSTALLATION_ID` or to pass the target repository.
  Every EXPECTED failure lands on the failure track as
  `GithubAppAuthError`; caller bugs propagate as built-ins. The
  returned token is ephemeral and MUST NOT be persisted at rest.

The `InstallationTokenProvider` and `credential_helper` contracts are unchanged: the provider mints with whatever `repository` its config carries, and the credential helper continues to resolve its config with no `repository`.

#### 2. `SPECIFICATION/scenarios.md` — amend three existing scenario bodies (headings unchanged)

`## Scenario: minting with a pinned installation performs no discovery` becomes:

```
Given a GithubAppConfig whose installation_id is "777" and whose repository is "thewoolleyman/livespec-runtime"
And MintSeams whose http_post answers POST /app/installations/777/access_tokens with a token
When mint_installation_token is invoked with that config and an issued_at
Then the result is an IOSuccess carrying that token
And the seams' http_get was never called, neither for the repository's installation nor for the App's installations
```

`## Scenario: minting discovers the sole installation when none is pinned` becomes:

```
Given a GithubAppConfig whose installation_id is None and whose repository is None
And MintSeams whose http_get answers GET /app/installations with exactly one installation, id 777
When mint_installation_token is invoked with that config
Then the seams' http_post targets /app/installations/777/access_tokens
And the result is an IOSuccess carrying the minted token
```

`## Scenario: minting with several installations and no pin fails closed directing the operator to pin one` becomes:

```
Given a GithubAppConfig whose installation_id is None and whose repository is None
And MintSeams whose http_get answers GET /app/installations with two installations
When mint_installation_token is invoked with that config
Then the result is an IOFailure carrying GithubAppAuthError
And the error's detail directs the operator to set GITHUB_APP_INSTALLATION_ID or to pass the target repository
And no access token is requested
```

#### 3. `SPECIFICATION/scenarios.md` — add these scenarios immediately after `## Scenario: minting with several installations and no pin fails closed directing the operator to pin one`

```
## Scenario: minting for a known repository resolves its installation from the repository

Given a GithubAppConfig whose installation_id is None and whose repository is "livespec-ai/livespec"
And MintSeams whose http_get answers GET /repos/livespec-ai/livespec/installation with an installation whose id is 182016479
When mint_installation_token is invoked with that config
Then the seams' http_post targets /app/installations/182016479/access_tokens
And the result is an IOSuccess carrying the minted token
And GET /app/installations was never requested, so a second installation of the App cannot make the mint ambiguous

## Scenario: minting for a repository the App is not installed on fails closed naming the repository

Given a GithubAppConfig with app_id "5761962", installation_id None and repository "livespec-ai/livespec"
And MintSeams whose http_get answers GET /repos/livespec-ai/livespec/installation with a failure, as GitHub does with 404 when the App is not installed there
When mint_installation_token is invoked with that config
Then the result is an IOFailure carrying GithubAppAuthError
And the error's detail names the repository "livespec-ai/livespec" and the App id "5761962"
And no access token is requested

## Scenario: one process mints for repositories of two owners from one environment

Given one environment mapping whose GITHUB_APP_OWNER_MAP maps "livespec-ai" to the org App pair and "thewoolleyman" to the personal App pair, with all four variables set
And MintSeams whose http_get answers GET /repos/livespec-ai/livespec/installation with id 182016479 and GET /repos/thewoolleyman/livespec-runtime/installation with id 131208965
When load_github_app_config is invoked for repository "livespec-ai/livespec" and for repository "thewoolleyman/livespec-runtime", and mint_installation_token is invoked with each resulting config in the same process
Then the first mint signs its App JWT with the org App's id and PEM and POSTs to /app/installations/182016479/access_tokens
And the second signs with the personal App's id and PEM and POSTs to /app/installations/131208965/access_tokens
And neither mint needs any environment override between the two calls
```

The revise that accepts this proposal MUST add one `tests/heading-coverage.json` row per new H2 in the same commit, per the revise co-edit discipline.
