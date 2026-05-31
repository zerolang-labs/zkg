## Registry Registration

For registry additions, this pull request should change only:

- `registry/<namespace>`
- `registry/index.tsv`

The namespace file must contain exactly one GitHub repository URL:

```text
https://github.com/<owner>/<repo>
```

The registry validation workflow checks namespace conflicts, index consistency,
request rate limits, and repository ownership or write/maintain/admin
permission for the package endpoint.
