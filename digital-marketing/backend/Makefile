PSQL=PGPASSWORD=admin /Library/PostgreSQL/18/bin/psql -U postgres -h localhost -d plugg

.PHONY: run build seed migrate-up migrate-down reset-db

run:
	cargo run --bin server

build:
	cargo build --release

seed:
	cargo run --bin seed

migrate-up:
	$(PSQL) -f migrations/000001_init_schema.up.sql

migrate-down:
	$(PSQL) -f migrations/000001_init_schema.down.sql

reset-db:
	$(PSQL) -c "TRUNCATE payments, concepts, bids, products, \
	             brand_profiles, influencer_profiles, users \
	             RESTART IDENTITY CASCADE;"
