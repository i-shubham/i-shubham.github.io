PYTHON=/opt/miniconda3/envs/myenv/bin/python

.PHONY: run seed migrate-up migrate-down install

run:
	$(PYTHON) run.py

install:
	$(PYTHON) -m pip install -r requirements.txt

seed:
	$(PYTHON) seed.py

migrate-up:
	PGPASSWORD=admin /Library/PostgreSQL/18/bin/psql -U postgres -h localhost -d plugg \
	  -f migrations/000001_init_schema.up.sql

migrate-down:
	PGPASSWORD=admin /Library/PostgreSQL/18/bin/psql -U postgres -h localhost -d plugg \
	  -f migrations/000001_init_schema.down.sql

reset-db:
	PGPASSWORD=admin /Library/PostgreSQL/18/bin/psql -U postgres -h localhost -d plugg \
	  -c "TRUNCATE payments, concepts, bids, products, brand_profiles, influencer_profiles, users RESTART IDENTITY CASCADE;"
