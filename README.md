# Wodby stacks

This repository is the index of Wodby-managed stack repositories for Wodby 2.0.

Stacks are application blueprints. A stack selects the
[services](https://github.com/wodby/services) an app should use and defines the
default configuration, links, versions, resources, and optional components for
those services.

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

### Data and search stacks

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
| Solr | [wodby/stack-solr](https://github.com/wodby/stack-solr) |
| ZooKeeper | [wodby/stack-zookeeper](https://github.com/wodby/stack-zookeeper) |

### Utilities and integrations

| Stack | Repository |
| --- | --- |
| Mailpit | [wodby/stack-mailpit](https://github.com/wodby/stack-mailpit) |
| OpenSMTPD | [wodby/stack-opensmtpd](https://github.com/wodby/stack-opensmtpd) |
| Gotenberg | [wodby/stack-gotenberg](https://github.com/wodby/stack-gotenberg) |
| FRPC | [wodby/stack-frpc](https://github.com/wodby/stack-frpc) |
| Tailscale | [wodby/stack-tailscale](https://github.com/wodby/stack-tailscale) |
| 3X UI | [wodby/stack-3xui](https://github.com/wodby/stack-3xui) |

### Kubernetes and platform stacks

| Stack | Repository |
| --- | --- |
| Envoy Gateway | [wodby/stack-envoy-gateway](https://github.com/wodby/stack-envoy-gateway) |
| Monitoring | [wodby/stack-monitoring](https://github.com/wodby/stack-monitoring) |
| Metrics | [wodby/stack-metrics](https://github.com/wodby/stack-metrics) |
| AWS LB Controller | [wodby/stack-aws-lb-controller](https://github.com/wodby/stack-aws-lb-controller) |
| OpenClaw | [wodby/stack-openclaw](https://github.com/wodby/stack-openclaw) |
