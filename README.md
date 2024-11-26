# Senya Web Backend

```bash
docker build -t senya-backend-app .
docker run -p 8000:8000 senya-backend-app
```

You can access:

API documentation at http://localhost:8000/docs
Alternative docs at http://localhost:8000/redoc
API root at http://localhost:8000

Test the API with curl:
```bash
# Test root endpoint
curl http://localhost:8000

# Test items endpoint
curl http://localhost:8000/items/5

# Create an item
curl -X POST http://localhost:8000/items/ \
    -H "Content-Type: application/json" \
    -d '{"name": "Widget", "price": 9.99}'
```

Python Venv
to activate:
```
source myenv/bin/activate
```
to deactivate:
```
deactivate
```

postgres:
```bash
docker-compose exec -it db psql -U senya -d senya_db
```

Alembic:
```bash
alembic init alembic # initialize alembic (only do this once)
alembic revision --autogenerate -m "initial migration" # create a new migration
alembic upgrade head # apply the migration
```