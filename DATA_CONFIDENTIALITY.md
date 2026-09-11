# Data Confidentiality Guide

Use this guide before adding data to the Lumen prototype.

## Public versus private data

Keep raw company data, customer records, real survey responses, internal sales, marketing spend, CAC, LTV, and channel economics in a private, access-controlled location. Do not commit them to this public repository.

The public demo should contain only synthetic data, aggregated statistics, public external data, and the application logic.

Treat the case data as confidential unless the data owner has confirmed that it is synthetic and approved for publication.

## Survey data

Do not publish or expose direct identifiers such as:

- first name
- last name
- email address
- respondent ID

For the demo, use aggregated fields such as segment, age band, city or region, preferred channel, price-sensitivity band, competitor awareness, and purchase-intent band. Suppress or combine small groups so that an individual cannot be identified from a result.

Replacing a name with an ID is pseudonymisation, not necessarily anonymisation. Keep the linkage file private, and do not send raw respondent rows to external APIs or AI tools without explicit approval.

## Recommended repository structure

- `data_demo/`: synthetic or aggregated data that is safe for the public prototype
- `private_data/`: local or private-repository data; never commit to this public repository
- application code: reads only the demo or approved data source

The deployed app must not expose raw survey files through an endpoint, client-side bundle, table, or download button.

## External services and APIs

Before sending data to an external service, confirm the provider, the exact fields being sent, the retention policy, and the firm's approval. Prefer local processing or pre-aggregated summaries. Keep API keys in environment variables or an approved secret manager, never in source files.

## If confidential data was committed

Deleting a file in a later commit does not remove it from Git history, forks, clones, pull requests, or cached views. Stop sharing the repository, notify the data owner, and follow the repository owner's incident process. Revoke or rotate any exposed credentials immediately. History rewriting and cleanup of other clones may be required.

## Sources

- [GitHub: Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [GitHub: Secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning)
- [European Data Protection Board: Anonymisation and pseudonymisation](https://www.edpb.europa.eu/topics/ai-and-technology/anonymisation-pseudonymisation_en)
- [EU GDPR, Article 5](https://eur-lex.europa.eu/eli/reg/2016/679/art_83/oj/eng)
