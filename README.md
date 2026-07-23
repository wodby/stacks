# Wodby stacks

This repository is the index of Wodby-managed stack repositories for Wodby 2.0.

Application stacks are reusable blueprints for user workloads. A stack selects
the [services](https://github.com/wodby/services) an app should use and defines
their default configuration, links, versions, resources, and optional
components.

Kubernetes system stacks are different: Wodby installs and manages them as
cluster infrastructure when required by the cluster provider and configuration.
They are not templates for user-deployed applications.

- Stack catalog: https://wodby.com/stacks
- Stack docs: https://wodby.com/docs/2.0/stacks/
- Stack template reference: https://wodby.com/docs/2.0/stacks/template/
- Stack boilerplate: https://github.com/wodby/stack

## Create a stack

Use the [stack boilerplate](https://github.com/wodby/stack) when you want to
create a custom Git-backed stack. It includes a valid `stack.yml` and README
guidance for stack service references, links, and overrides.

For a single stack repository, put `stack.yml` at the repository root. For a
repository that contains multiple stacks, add an `index.yml` with stack
directories:

```yaml
stacks:
- api
- worker
```

Before publishing a stack for others to use, review:

- [Stack template reference](https://wodby.com/docs/2.0/stacks/template/)
- [Stack services](https://wodby.com/docs/2.0/stacks/services/)
- [Stack updates](https://wodby.com/docs/2.0/stacks/updates/)
- [Naming rules](https://wodby.com/docs/2.0/naming/)

## Repository presentation

[`scripts/update_repository_readmes.py`](scripts/update_repository_readmes.py)
renders the README in every indexed `stack-*` repository. It resolves service
references, links compatible source templates and service repositories, and
classifies any stack containing an infrastructure service as a Kubernetes
system stack.
The aggregate, service, and stack repositories must be checked out as sibling
directories, and the script requires PyYAML.

```bash
python scripts/update_repository_readmes.py --check
python scripts/update_repository_readmes.py --write
```

[`scripts/update_github_metadata.py`](scripts/update_github_metadata.py) applies
the same classification to GitHub descriptions, topics, and catalog homepages.
It requires the GitHub CLI and `WODBY_GITHUB_TOKEN`.

```bash
python scripts/update_github_metadata.py --check
python scripts/update_github_metadata.py --write
```

## Managed stacks

### Application stacks

| Stack | Repository |
| --- | --- |
| HTML | [wodby/stack-html](https://github.com/wodby/stack-html) |
| PHP | [wodby/stack-php](https://github.com/wodby/stack-php) |
| Drupal | [wodby/stack-drupal](https://github.com/wodby/stack-drupal) |
| WordPress | [wodby/stack-wordpress](https://github.com/wodby/stack-wordpress) |
| Laravel | [wodby/stack-laravel](https://github.com/wodby/stack-laravel) |
| Matomo | [wodby/stack-matomo](https://github.com/wodby/stack-matomo) |
| Python | [wodby/stack-python](https://github.com/wodby/stack-python) |
| Django | [wodby/stack-django](https://github.com/wodby/stack-django) |
| FastAPI | [wodby/stack-fastapi](https://github.com/wodby/stack-fastapi) |
| Flask | [wodby/stack-flask](https://github.com/wodby/stack-flask) |
| Ruby | [wodby/stack-ruby](https://github.com/wodby/stack-ruby) |
| Rails | [wodby/stack-rails](https://github.com/wodby/stack-rails) |
| Go | [wodby/stack-go](https://github.com/wodby/stack-go) |
| Node.js | [wodby/stack-node](https://github.com/wodby/stack-node) |
| Next.js | [wodby/stack-nextjs](https://github.com/wodby/stack-nextjs) |
| Dagster | [wodby/stack-dagster](https://github.com/wodby/stack-dagster) |

### Data, messaging, and search stacks

| Stack | Repository |
| --- | --- |
| MariaDB | [wodby/stack-mariadb](https://github.com/wodby/stack-mariadb) |
| PostgreSQL | [wodby/stack-postgres](https://github.com/wodby/stack-postgres) |
| PostGIS | [wodby/stack-postgis](https://github.com/wodby/stack-postgis) |
| Cloud MySQL | [wodby/stack-cloud-mysql](https://github.com/wodby/stack-cloud-mysql) |
| Cloud MariaDB | [wodby/stack-cloud-mariadb](https://github.com/wodby/stack-cloud-mariadb) |
| Cloud PostgreSQL | [wodby/stack-cloud-postgres](https://github.com/wodby/stack-cloud-postgres) |
| Valkey | [wodby/stack-valkey](https://github.com/wodby/stack-valkey) |
| Redis | [wodby/stack-redis](https://github.com/wodby/stack-redis) |
| RabbitMQ | [wodby/stack-rabbitmq](https://github.com/wodby/stack-rabbitmq) |
| Solr | [wodby/stack-solr](https://github.com/wodby/stack-solr) |
| ZooKeeper | [wodby/stack-zookeeper](https://github.com/wodby/stack-zookeeper) |

### Utilities and integrations

| Stack | Repository |
| --- | --- |
| Mailpit | [wodby/stack-mailpit](https://github.com/wodby/stack-mailpit) |
| OpenSMTPD | [wodby/stack-opensmtpd](https://github.com/wodby/stack-opensmtpd) |
| Gotenberg | [wodby/stack-gotenberg](https://github.com/wodby/stack-gotenberg) |
| Tailscale | [wodby/stack-tailscale](https://github.com/wodby/stack-tailscale) |
| 3X UI | [wodby/stack-3xui](https://github.com/wodby/stack-3xui) |
| OpenClaw | [wodby/stack-openclaw](https://github.com/wodby/stack-openclaw) |

### Observability app stacks

| Stack | Repository |
| --- | --- |
| Prometheus | [wodby/stack-prometheus](https://github.com/wodby/stack-prometheus) |

### Kubernetes system stacks

Wodby provisions these stacks as Kubernetes system apps. Their availability and
configuration depend on the cluster provider and selected infrastructure
features.

| Stack | Repository |
| --- | --- |
| Envoy Gateway | [wodby/stack-envoy-gateway](https://github.com/wodby/stack-envoy-gateway) |
| Monitoring | [wodby/stack-monitoring](https://github.com/wodby/stack-monitoring) |
| Metrics | [wodby/stack-metrics](https://github.com/wodby/stack-metrics) |
| AWS LB Controller | [wodby/stack-aws-lb-controller](https://github.com/wodby/stack-aws-lb-controller) |
| FRPC | [wodby/stack-frpc](https://github.com/wodby/stack-frpc) |
