package repository

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smallick/plugg-backend/internal/models"
)

type BrandRepo struct {
	DB *pgxpool.Pool
}

func (r *BrandRepo) Create(ctx context.Context, b *models.BrandProfile) error {
	_, err := r.DB.Exec(ctx,
		`INSERT INTO brand_profiles (user_id, company, industry, website, about, logo)
		 VALUES ($1,$2,$3,$4,$5,$6)`,
		b.UserID, b.Company, b.Industry, b.Website, b.About, b.Logo,
	)
	return err
}

func (r *BrandRepo) GetByUserID(ctx context.Context, userID int64) (*models.BrandProfile, error) {
	b := &models.BrandProfile{}
	err := r.DB.QueryRow(ctx,
		`SELECT user_id, company, industry, website, about, logo
		 FROM brand_profiles WHERE user_id = $1`, userID,
	).Scan(&b.UserID, &b.Company, &b.Industry, &b.Website, &b.About, &b.Logo)
	if err != nil {
		return nil, err
	}
	return b, nil
}
