# zkg Registry

This directory is the first-class package registry for `zkg`.

The registry is only a name server. It maps a Zero namespace alias to a URL
endpoint and does not store package source code.

## Entry Format

Each package entry is a plain text file named after the namespace:

```text
registry/<owner>.<package>
```

The file content is exactly one URL endpoint:

```text
https://github.com/<owner>/<repo>
```

`registry/index.tsv` is the search index used by `zkg search`.

## Namespace Rules

Namespaces must:

- be lowercase Zero module identifiers separated by `.`
- contain at least two segments, such as `user.repo`
- use only `a-z`, `0-9`, and `_`
- not conflict with an existing file in this directory or row in `index.tsv`

## Registration

Open a pull request that adds:

- `registry/<namespace>` containing exactly one GitHub repository URL
- one sorted row in `registry/index.tsv`

This follows the js.org-style contribution model: the requested namespace is
reviewed as code, and the registry is updated only by merging the pull request.

The registry PR workflow validates:

- ownership or write/maintain/admin permission for the endpoint repository
- requester rate limits
- namespace conflicts
- `registry/index.tsv` consistency
- that registry entries remain URL endpoints only, not package contents
