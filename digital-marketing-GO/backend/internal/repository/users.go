package repository

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smallick/plugg-backend/internal/models"
)

type UserRepo struct {
	DB *pgxpool.Pool
}

func (r *UserRepo) Create(ctx context.Context, u *models.User) error {
	return r.DB.QueryRow(ctx,
		`INSERT INTO users (role, name, email, password_hash, created_at)
		 VALUES ($1, $2, $3, $4, $5) RETURNING id`,
		u.Role, u.Name, u.Email, u.PasswordHash, time.Now(),
	).Scan(&u.ID)
}

func (r *UserRepo) GetByEmail(ctx context.Context, email string) (*models.User, error) {
	u := &models.User{}
	err := r.DB.QueryRow(ctx,
		`SELECT id, role, name, email, password_hash, created_at FROM users WHERE email = $1`,
		email,
	).Scan(&u.ID, &u.Role, &u.Name, &u.Email, &u.PasswordHash, &u.CreatedAt)
	if err != nil {
		return nil, err
	}
	return u, nil
}

func (r *UserRepo) GetByID(ctx context.Context, id int64) (*models.User, error) {
	u := &models.User{}
	err := r.DB.QueryRow(ctx,
		`SELECT id, role, name, email, password_hash, created_at FROM users WHERE id = $1`,
		id,
	).Scan(&u.ID, &u.Role, &u.Name, &u.Email, &u.PasswordHash, &u.CreatedAt)
	if err != nil {
		return nil, err
	}
	return u, nil
}
