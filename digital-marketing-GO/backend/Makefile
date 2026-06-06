MIGRATE_BIN=go run -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest
DB_URL ?= postgres://postgres:postgres@localhost:5432/plugg?sslmode=disable

.PHONY: run build migrate-up migrate-down migrate-create tidy

run:
	go run ./cmd/server

build:
	go build -o bin/plugg-server ./cmd/server

tidy:
	go mod tidy

migrate-up:
	$(MIGRATE_BIN) -path migrations -database "$(DB_URL)" up

migrate-down:
	$(MIGRATE_BIN) -path migrations -database "$(DB_URL)" down 1

migrate-create:
	$(MIGRATE_BIN) create -ext sql -dir migrations -seq $(name)

seed:
	go run ./cmd/seed
