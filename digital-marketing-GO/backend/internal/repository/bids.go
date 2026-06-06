package repository

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smallick/plugg-backend/internal/models"
)

type BidRepo struct {
	DB *pgxpool.Pool
}

func (r *BidRepo) Create(ctx context.Context, b *models.Bid) error {
	return r.DB.QueryRow(ctx,
		`INSERT INTO bids (product_id, influencer_user_id, amount, message, status, created_at)
		 VALUES ($1,$2,$3,$4,'pending',$5) RETURNING id`,
		b.ProductID, b.InfluencerUserID, b.Amount, b.Message, time.Now(),
	).Scan(&b.ID)
}

func (r *BidRepo) ListByProduct(ctx context.Context, productID int64) ([]models.Bid, error) {
	rows, err := r.DB.Query(ctx,
		`SELECT b.id, b.product_id, b.influencer_user_id, b.amount, b.message, b.status, b.created_at,
		        COALESCE(u.name,'') AS influencer_name,
		        COALESCE(ip.handle,'') AS influencer_handle,
		        COALESCE(ip.avatar,'') AS influencer_avatar
		 FROM bids b
		 LEFT JOIN users u ON u.id = b.influencer_user_id
		 LEFT JOIN influencer_profiles ip ON ip.user_id = b.influencer_user_id
		 WHERE b.product_id = $1 ORDER BY b.created_at DESC`, productID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var list []models.Bid
	for rows.Next() {
		var b models.Bid
		if err := rows.Scan(
			&b.ID, &b.ProductID, &b.InfluencerUserID, &b.Amount, &b.Message, &b.Status, &b.CreatedAt,
			&b.InfluencerName, &b.InfluencerHandle, &b.InfluencerAvatar,
		); err != nil {
			return nil, err
		}
		list = append(list, b)
	}
	return list, nil
}

func (r *BidRepo) ListByInfluencer(ctx context.Context, influencerUserID int64) ([]models.Bid, error) {
	rows, err := r.DB.Query(ctx,
		`SELECT id, product_id, influencer_user_id, amount, message, status, created_at
		 FROM bids WHERE influencer_user_id = $1 ORDER BY created_at DESC`, influencerUserID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var list []models.Bid
	for rows.Next() {
		var b models.Bid
		if err := rows.Scan(&b.ID, &b.ProductID, &b.InfluencerUserID, &b.Amount, &b.Message, &b.Status, &b.CreatedAt); err != nil {
			return nil, err
		}
		list = append(list, b)
	}
	return list, nil
}

func (r *BidRepo) GetByID(ctx context.Context, id int64) (*models.Bid, error) {
	b := &models.Bid{}
	err := r.DB.QueryRow(ctx,
		`SELECT id, product_id, influencer_user_id, amount, message, status, created_at
		 FROM bids WHERE id = $1`, id,
	).Scan(&b.ID, &b.ProductID, &b.InfluencerUserID, &b.Amount, &b.Message, &b.Status, &b.CreatedAt)
	if err != nil {
		return nil, err
	}
	return b, nil
}

func (r *BidRepo) UpdateStatus(ctx context.Context, id int64, status string) error {
	_, err := r.DB.Exec(ctx, `UPDATE bids SET status=$1 WHERE id=$2`, status, id)
	return err
}

func (r *BidRepo) RejectOthers(ctx context.Context, productID, approvedBidID int64) error {
	_, err := r.DB.Exec(ctx,
		`UPDATE bids SET status='rejected' WHERE product_id=$1 AND id != $2 AND status='pending'`,
		productID, approvedBidID)
	return err
}

func (r *BidRepo) ExistsByInfluencerAndProduct(ctx context.Context, influencerUserID, productID int64) (bool, error) {
	var exists bool
	err := r.DB.QueryRow(ctx,
		`SELECT EXISTS(SELECT 1 FROM bids WHERE influencer_user_id=$1 AND product_id=$2)`,
		influencerUserID, productID,
	).Scan(&exists)
	return exists, err
}
