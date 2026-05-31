# zkg

`zkg` is a small package manager for Zero projects.

It vendors a GitHub-hosted Zero package into the current package under
`src/zkg/`, so package code can be imported with Zero's package-local module
resolver.

## Install

Install from the hosted repository:

```sh
git clone https://github.com/zerolang-labs/zkg.git
cd zkg
./setup.sh install
```

The implementation under `src/` uses Zero standard modules for filesystem and
HTTP work: `std.fs`, `std.http`, `std.net`, and `std.path`. The root
`setup.sh` file is only a bootstrapper that delegates to `zero run`; it does
not clone, copy, remove, or fetch package contents itself.

## Add A Package

Run `zkg add` from the root of the package that should receive the dependency:

```sh
zkg add https://github.com/user/repo
```

Search the first-class zkg registry:

```sh
zkg search
zkg search wgpu
```

Install from a registry alias instead of a full HTTP URL:

```sh
zkg add ihasq.wgpu_zero
zkg install ihasq.wgpu_zero
```

This creates an importable module tree under `src/zkg/`:

```zero
use zkg.user.repo
```

Registry aliases are resolved from this repository's `registry/` directory on
GitHub. The registry is a name server only: it maps aliases to URL endpoints and
does not store package source code.

Repository owner, package names, and aliases should already be valid Zero module
identifiers for the standard-module implementation.

If the upstream repository has `src/mod.0`, that remains the module entry point.
If it only has `src/lib.0` or `src/main.0`, `zkg` moves that file to `mod.0` so
the `use zkg.user.repo` form resolves.

The standard-module implementation fetches package source over `std.http`
instead of invoking `git`.

## Registry

`./registry` is the zkg equivalent of the crates.io namespace layer. It is
intentionally small:

```text
registry/
  index.tsv          search index used by zkg search
  <namespace>        one URL endpoint per alias
```

For example, `registry/ihasq.wgpu_zero` contains:

```text
https://github.com/ihasq/wgpu-zero
```

Volunteers register new aliases by opening a pull request, following the
js.org-style contribution model. A registration PR adds only
`registry/<namespace>` and the matching sorted `registry/index.tsv` row. The
GitHub Actions registry PR workflow validates:

- requester rate limits
- namespace conflicts
- repository ownership or write/maintain/admin permission

Merged PRs are the only way registry metadata changes.

## Remove A Package

`zkg remove` removes a vendored package namespace from the current project.
The namespace is relative to `src/zkg`, so omit the `zkg.` import prefix:

```sh
zkg remove user.repo
```

Removal deletes the vendored module entry under `src/zkg/` using `std.fs`.

## Update And Uninstall

Update the global `zkg` command to the latest version:

```sh
zkg update
```

`zkg update` uses `std.http` to fetch the latest repository metadata into
`.zkg/cache`.

Uninstall a globally installed command by the command name used to run it:

```sh
zkg uninstall zkg
```

For `zkg`, this removes `.zkg/bin/zkg` when present.

## ZKG_HOME

The standard-module implementation uses a project-local `.zkg` directory.

```text
.zkg/
  bin/                    command records prepared by zkg install
  cache/                  HTTP-fetched metadata
  packages/               package metadata written by zkg add
```

## Development

The package manager implementation is written in `.0` under `src/`.

```sh
zero check .
zero test .
```

Zero 0.2.0 can check this package. On this Linux host, `zero run .` is still
blocked by the current host executable backend, so runtime use depends on a Zero
build that can run hosted programs with `std.fs` and `std.http`.
