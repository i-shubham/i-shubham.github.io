package handlers

import (
	"context"
	"net/http"

	"github.com/jackc/pgx/v5/pgxpool"
)

type StatsHandler struct {
	DB *pgxpool.Pool
}

func (h *StatsHandler) PublicStats(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	stats := map[string]interface{}{
		"creators":  countWhere(ctx, h.DB, "users", "role='influencer'"),
		"brands":    countWhere(ctx, h.DB, "users", "role='brand'"),
		"campaigns": countWhere(ctx, h.DB, "products", "1=1"),
		"bids":      countWhere(ctx, h.DB, "bids", "1=1"),
		"approved":  countWhere(ctx, h.DB, "bids", "status='approved'"),
	}

	approved := stats["approved"].(int)
	delivered := 0
	if approved > 0 {
		delivered = countWhere(ctx, h.DB, "concepts", "1=1")
	}
	if approved > 0 {
		stats["delivery"] = (delivered * 100) / approved
	} else {
		stats["delivery"] = 100
	}

	writeJSON(w, http.StatusOK, stats)
}

func countWhere(ctx context.Context, db *pgxpool.Pool, table, where string) int {
	var n int
	_ = db.QueryRow(ctx, "SELECT COUNT(*) FROM "+table+" WHERE "+where).Scan(&n)
	return n
}
