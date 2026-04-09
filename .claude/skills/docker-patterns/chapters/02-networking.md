# Networking

> 상위 스킬: [docker-patterns](../SKILL.md)

### Service Discovery

Services in the same Compose network resolve by service name:
```
# From "app" container:
postgres://postgres:postgres@db:5432/app_dev    # "db" resolves to the db container
redis://redis:6379/0                             # "redis" resolves to the redis container
```

### Custom Networks

```yaml
services:
  frontend:
    networks:
      - frontend-net

  api:
    networks:
      - frontend-net
      - backend-net

  db:
    networks:
      - backend-net              # Only reachable from api, not frontend

networks:
  frontend-net:
  backend-net:
```

### Exposing Only What's Needed

```yaml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"   # Only accessible from host, not network
    # Omit ports entirely in production -- accessible only within Docker network
```
