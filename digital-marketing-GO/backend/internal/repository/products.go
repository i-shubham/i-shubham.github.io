package repository

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smallick/plugg-backend/internal/models"
)

type ProductRepo struct {
	DB *pgxpool.Pool
}

func (r *ProductRepo) Create(ctx context.Context, p *models.Product) error {
	return r.DB.QueryRow(ctx,
		`INSERT INTO products (brand_user_id, title, description, category, budget, deadline, deliverables, status, created_at)
		 VALUES ($1,$2,$3,$4,$5,$6,$7,'open',$8) RETURNING id`,
		p.BrandUserID, p.Title, p.Description, p.Category, p.Budget, p.Deadline, p.Deliverables, time.Now(),
	).Scan(&p.ID)
}

func (r *ProductRepo) List(ctx context.Context) ([]models.Product, error) {
	rows, err := r.DB.Query(ctx,
		`SELECT p.id, p.brand_user_id, p.title, p.description, p.category, p.budget,
		        p.deadline, p.deliverables, p.status, p.created_at,
		        COALESCE(b.company,'') AS brand_name, COALESCE(b.logo,'') AS brand_logo
		 FROM products p
		 LEFT JOIN brand_profiles b ON b.user_id = p.brand_user_id
		 ORDER BY p.created_at DESC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var list []models.Product
	for rows.Next() {
		var p models.Product
		if err := rows.Scan(
			&p.ID, &p.BrandUserID, &p.Title, &p.Description, &p.Category, &p.Budget,
			&p.Deadline, &p.Deliverables, &p.Status, &p.CreatedAt,
			&p.BrandName, &p.BrandLogo,
		); err != nil {
			return nil, err
		}
		list = append(list, p)
	}
	return list, nil
}

func (r *ProductRepo) GetByID(ctx context.Context, id int64) (*models.Product, error) {
	p := &models.Product{}
	err := r.DB.QueryRow(ctx,
		`SELECT p.id, p.brand_user_id, p.title, p.description, p.category, p.budget,
		        p.deadline, p.deliverables, p.status, p.created_at,
		        COALESCE(b.company,'') AS brand_name, COALESCE(b.logo,'') AS brand_logo
		 FROM products p
		 LEFT JOIN brand_profiles b ON b.user_id = p.brand_user_id
		 WHERE p.id = $1`, id,
	).Scan(
		&p.ID, &p.BrandUserID, &p.Title, &p.Description, &p.Category, &p.Budget,
		&p.Deadline, &p.Deliverables, &p.Status, &p.CreatedAt,
		&p.BrandName, &p.BrandLogo,
	)
	if err != nil {
		return nil, err
	}
	return p, nil
}

func (r *ProductRepo) ListByBrand(ctx context.Context, brandUserID int64) ([]models.Product, error) {
	rows, err := r.DB.Query(ctx,
		`SELECT id, brand_user_id, title, description, category, budget, deadline, deliverables, status, created_at
		 FROM products WHERE brand_user_id = $1 ORDER BY created_at DESC`, brandUserID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var list []models.Product
	for rows.Next() {
		var p models.Product
		if err := rows.Scan(
			&p.ID, &p.BrandUserID, &p.Title, &p.Description, &p.Category, &p.Budget,
			&p.Deadline, &p.Deliverables, &p.Status, &p.CreatedAt,
		); err != nil {
			return nil, err
		}
		list = append(list, p)
	}
	return list, nil
}

func (r *ProductRepo) UpdateStatus(ctx context.Context, id int64, status string) error {
	_, err := r.DB.Exec(ctx, `UPDATE products SET status=$1 WHERE id=$2`, status, id)
	return err
}
