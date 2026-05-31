# zkg Registry

This directory is the first-class package registry for `zkg`.

The registry is only a name server. It maps a Zero package name to a URL
endpoint and does not store package source code.

## Entry Format

Each package entry is a plain text file named after the package:

```text
registry/<package-name>
```

The file content is exactly one URL endpoint:

```text
https://github.com/<owner>/<repo>
```

`registry/index.tsv` is the search index used by `zkg search`.

## Namespace Rules

Package names must:

- match endpoint `zero.json` `package.name`
- be a lowercase Zero module identifier
- use only `a-z`, `0-9`, and `_`
- not conflict with an existing file in this directory or row in `index.tsv`

## Registration

Open a pull request that adds:

- `registry/<package-name>` containing exactly one GitHub repository URL
- one sorted row in `registry/index.tsv`

This follows the js.org-style contribution model: the requested package name is
reviewed as code, and the registry is updated only by merging the pull request.

The registry PR workflow validates:

- ownership or write/maintain/admin permission for the endpoint repository
- requester rate limits
- package name conflicts
- `registry/index.tsv` consistency
- endpoint `zero.json` `package.name` matches `registry/<package-name>`
- endpoint Zero code with `zero check`
- that registry entries remain URL endpoints only, not package contents
