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

Install from a registry package name instead of a full HTTP URL:

```sh
zkg add wgpu
zkg install wgpu
```

This creates an importable module tree under `src/zkg/`:

```zero
use zkg.wgpu
```

Registry package names are resolved from this repository's `registry/`
directory on GitHub. The registry is a name server only: it maps package names
to URL endpoints and does not store package source code.

Package names come from endpoint `zero.json` `package.name` and must be valid
Zero module identifiers for the standard-module implementation.

If the upstream repository has `src/mod.0`, that remains the module entry point.
If it only has `src/lib.0` or `src/main.0`, `zkg` moves that file to `mod.0` so
the `use zkg.<package>` form resolves.

The standard-module implementation fetches package source over `std.http`
instead of invoking `git`.

## Registry

`./registry` is the zkg equivalent of the crates.io package-name layer. It is
intentionally small:

```text
registry/
  index.tsv          search index used by zkg search
  <package-name>     one URL endpoint per package name
```

A registration for `wgpu` would add `registry/wgpu` containing:

```text
https://github.com/ihasq/wgpu-zero
```

Volunteers register new package names by opening a pull request, following the
js.org-style contribution model. A registration PR adds only
`registry/<package-name>` and the matching sorted `registry/index.tsv` row. The
GitHub Actions registry PR workflow validates:

- requester rate limits
- package name conflicts
- repository ownership or write/maintain/admin permission
- endpoint `zero.json` `package.name` matches `registry/<package-name>`
- endpoint Zero code with `zero check`

Merged PRs are the only way registry metadata changes.

## Remove A Package

`zkg remove` removes a vendored package from the current project. The package
name is relative to `src/zkg`, so omit the `zkg.` import prefix:

```sh
zkg remove wgpu
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
