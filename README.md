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

This creates an importable module tree under `src/zkg/`:

```zero
use zkg.user.repo
```

Repository owner and name segments should already be valid Zero module
identifiers for the standard-module implementation.

If the upstream repository has `src/mod.0`, that remains the module entry point.
If it only has `src/lib.0` or `src/main.0`, `zkg` moves that file to `mod.0` so
the `use zkg.user.repo` form resolves.

The standard-module implementation fetches package source over `std.http`
instead of invoking `git`.

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
