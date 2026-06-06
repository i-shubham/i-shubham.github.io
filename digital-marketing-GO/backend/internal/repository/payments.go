package repository

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smallick/plugg-backend/internal/models"
)

type PaymentRepo struct {
	DB *pgxpool.Pool
}

func (r *PaymentRepo) Create(ctx context.Context, p *models.Payment) error {
	return r.DB.QueryRow(ctx,
		`INSERT INTO payments (type, user_id, ref_id, gross, amount, status, note, created_at)
		 VALUES ($1,$2,$3,$4,$5,'completed',$6,$7) RETURNING id`,
		p.Type, p.UserID, p.RefID, p.Gross, p.Amount, p.Note, time.Now(),
	).Scan(&p.ID)
}

func (r *PaymentRepo) AdminRevenue(ctx context.Context) (*models.AdminRevenue, error) {
	rev := &models.AdminRevenue{}

	err := r.DB.QueryRow(ctx,
		`SELECT COALESCE(SUM(CASE WHEN type='brand_commission' THEN amount ELSE 0 END),0),
		        COALESCE(SUM(CASE WHEN type='influencer_subscription' THEN amount ELSE 0 END),0),
		        COALESCE(SUM(CASE WHEN type='influencer_commission' THEN amount ELSE 0 END),0)
		 FROM payments WHERE status='completed'`,
	).Scan(&rev.BrandCommissions, &rev.InfluencerSubscriptions, &rev.InfluencerCommissions)
	if err != nil {
		return nil, err
	}
	rev.TotalRevenue = rev.BrandCommissions + rev.InfluencerSubscriptions + rev.InfluencerCommissions

	rows, err := r.DB.Query(ctx,
		`SELECT id, type, user_id, ref_id, gross, amount, status, note, created_at
		 FROM payments ORDER BY created_at DESC LIMIT 20`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var p models.Payment
		if err := rows.Scan(&p.ID, &p.Type, &p.UserID, &p.RefID, &p.Gross, &p.Amount, &p.Status, &p.Note, &p.CreatedAt); err != nil {
			return nil, err
		}
		rev.RecentPayments = append(rev.RecentPayments, p)
	}
	return rev, nil
}
