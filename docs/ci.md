# CI and GitHub synchronization

Push changes to the primary
[Forgejo repository](https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots).
Its `.forgejo/workflows/ci.yml` runs these checks:

- Publishable files pass the privacy scanner.
- The prebuilt TUI matches `VERSION`, its frontend source and binary checksums.
- Pinned editor assets match their recorded fingerprints.
- Python and Go checks pass using temporary homes and fixtures.

Successful push or manual runs then synchronize Git branches and tags to
[Fi3w0/Fiw-Gentoo-Dots on GitHub](https://github.com/Fi3w0/Fiw-Gentoo-Dots).
Pull request runs perform checks without mirroring. GitHub's separate workflow
runs the same checks on received pushes and pull requests.

The runner uses a Debian container with Python 3.11 and pinned Go 1.26.7.
Remote checkout/setup actions use fixed commit IDs. CI checks the installer
code without installing Gentoo packages, applying live desktop configs or
deploying bootloaders. It verifies the existing release bundle; changing
frontend source requires rebuilding and committing its matching bundle.

## Forgejo setup

Repository Actions must be enabled and an available runner must match
`docker`. If your runner has another label, set the Forgejo repository
Actions variable `CI_RUNNER_LABEL` to that label. The runner needs Docker to
execute the workflow's container jobs. See the
[Forgejo 10 Actions guide](https://forgejo.org/docs/v10.0/user/actions/) for
runner and secret settings used by this instance.

Add the repository Actions secret **`GH_MIRROR_SSH_KEY`** with the complete
private SSH deploy key registered on the GitHub mirror. The initial key is
stored locally at `local/ci/github-mirror`, outside version control. The
corresponding GitHub deploy key is named **Forgejo mirror**, with write access.
GitHub documents [deploy key management](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys).
The workflow exposes the key only to the mirroring step and uses a temporary
mode-600 key file, removed when the process exits. GitHub's Ed25519 host key
is pinned in `tools/ci/github_known_hosts` from its authenticated metadata API.

The **Run workflow** action retries synchronization after adding a secret or
runner. Pushing another commit also triggers it.

## Sync behaviour

The mirror fetches the current source repository and checks that the triggering
ref still points to the commit reviewed by that CI run. Superseded runs skip
publication. Branches and annotated tags keep their original history and IDs.
Pushes are atomic and use ordinary fast-forward rules. Divergent GitHub edits
cause an error for review. GitHub-only refs and refs deleted at the source are
retained. Keep normal development on Forgejo to maintain a consistent mirror.

For an explicit manual sync with the initial local deploy key:

```sh
python3 tools/ci/mirror.py --key-file local/ci/github-mirror
```

The shared check command is:

```sh
python3 tools/ci/check.py
```
