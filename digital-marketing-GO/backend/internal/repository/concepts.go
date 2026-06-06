package repository

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smallick/plugg-backend/internal/models"
)

type ConceptRepo struct {
	DB *pgxpool.Pool
}

func (r *ConceptRepo) Create(ctx context.Context, c *models.Concept) error {
	return r.DB.QueryRow(ctx,
		`INSERT INTO concepts (bid_id, product_id, brand_user_id, influencer_user_id, concept, script, deliverables, deadline, shared_at)
		 VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING id`,
		c.BidID, c.ProductID, c.BrandUserID, c.InfluencerUserID, c.Concept, c.Script, c.Deliverables, c.Deadline, time.Now(),
	).Scan(&c.ID)
}

func (r *ConceptRepo) GetByBidID(ctx context.Context, bidID int64) (*models.Concept, error) {
	c := &models.Concept{}
	err := r.DB.QueryRow(ctx,
		`SELECT id, bid_id, product_id, brand_user_id, influencer_user_id, concept, script, deliverables, deadline, shared_at
		 FROM concepts WHERE bid_id = $1`, bidID,
	).Scan(&c.ID, &c.BidID, &c.ProductID, &c.BrandUserID, &c.InfluencerUserID, &c.Concept, &c.Script, &c.Deliverables, &c.Deadline, &c.SharedAt)
	if err != nil {
		return nil, err
	}
	return c, nil
}
