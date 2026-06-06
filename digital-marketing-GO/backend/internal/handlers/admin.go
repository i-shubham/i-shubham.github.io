package handlers

import (
	"net/http"

	"github.com/smallick/plugg-backend/internal/repository"
)

type AdminHandler struct {
	Payments *repository.PaymentRepo
}

func (h *AdminHandler) Revenue(w http.ResponseWriter, r *http.Request) {
	rev, err := h.Payments.AdminRevenue(r.Context())
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to fetch revenue")
		return
	}
	writeJSON(w, http.StatusOK, rev)
}
