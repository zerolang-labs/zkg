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
./zkg install
```

This validates the `.0` source with `zero check .` and installs the command at:

```text
~/.zkg/bin/zkg
```

Add `~/.zkg/bin` to `PATH` if the installer prints that hint.

## Add A Package

Run `zkg add` from the root of the package that should receive the dependency:

```sh
zkg add https://github.com/user/repo
```

This creates an importable module tree under `src/zkg/`:

```zero
use zkg.user.repo
```

Repository owner and name segments are normalized to Zero identifiers: `-` and
`.` become `_`, and a leading digit gets a leading `_`. For example:

```sh
zkg add https://github.com/ihasq/wgpu-zero
```

is imported as:

```zero
use zkg.ihasq.wgpu_zero
```

If the upstream repository has `src/mod.0`, that remains the module entry point.
If it only has `src/lib.0` or `src/main.0`, `zkg` moves that file to `mod.0` so
the `use zkg.user.repo` form resolves.

If the upstream package has an `include/` directory, `zkg add` copies it into
the receiving package root so vendored `extern c "include/..."` imports can be
checked from the consumer package.

## Remove A Package

`zkg remove` removes a vendored package namespace from the current project.
The namespace is relative to `src/zkg`, so omit the `zkg.` import prefix:

```sh
zkg remove user.repo
```

For the `wgpu-zero` example:

```sh
zkg remove ihasq.wgpu_zero
```

Removal deletes the vendored module directory under `src/zkg/`, the matching
project lock record, matching global metadata under `~/.zkg/packages/`, and the
matching clone cache under `~/.zkg/cache/`.

## Update And Uninstall

Update the global `zkg` command to the latest version:

```sh
zkg update
```

When run from a zkg source checkout, `zkg update` runs `git pull --ff-only` and
then reinstalls. When run from the globally installed command, it updates or
clones the upstream source into `~/.zkg/tmp/zkg-source` and reinstalls from
there. Set `ZKG_UPDATE_URL` to override the upstream repository.

Uninstall a globally installed command by the command name used to run it:

```sh
zkg uninstall zkg
```

For `zkg`, this removes `~/.zkg/bin/zkg` and the installed source snapshot.

## ZKG_HOME

By default `zkg` uses `~/.zkg`. Set `ZKG_HOME` to override it.

```text
~/.zkg/
  bin/zkg                 globally installed command
  cache/github/user/repo  clone cache used by zkg add
  packages/user/repo.json global package metadata
  src/                    source snapshot installed by zkg install
  tmp/zkg-source          update checkout used by zkg update
  version                 installed source commit when available
  source-url              update source URL when available
```

## Development

The package manager implementation is written in `.0` under `src/`.

```sh
zero check .
zero test .
```

Zero 0.2.0 can check this package, but the current Linux host executable backend
cannot yet emit a host binary that uses `std.proc`. For day-to-day use this
repository includes the thin `./zkg` command with the same install layout.
