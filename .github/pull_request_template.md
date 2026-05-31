## Registry Registration

For registry additions, this pull request should change only:

- `registry/<package-name>`
- `registry/index.tsv`

The package file must contain exactly one GitHub repository URL:

```text
https://github.com/<owner>/<repo>
```

The registry validation workflow checks package name conflicts, index
consistency, request rate limits, and repository ownership or write/maintain/admin
permission for the package endpoint. It also clones the endpoint repository and
requires `zero.json` `package.name` to match `registry/<package-name>` before
running `zero check`.
