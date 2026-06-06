package handlers

import (
	"net/http"
	"strconv"

	"github.com/smallick/plugg-backend/internal/middleware"
	"github.com/smallick/plugg-backend/internal/models"
	"github.com/smallick/plugg-backend/internal/repository"
)

type PaymentHandler struct {
	Payments    *repository.PaymentRepo
	Influencers *repository.InfluencerRepo
}

func (h *PaymentHandler) RecordPayment(w http.ResponseWriter, r *http.Request) {
	idStr := middleware.GetUserID(r.Context())
	userID, _ := strconv.ParseInt(idStr, 10, 64)

	var req models.RecordPaymentRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	payment := &models.Payment{
		Type:   req.Type,
		UserID: userID,
		RefID:  req.RefID,
		Gross:  req.Gross,
		Amount: req.Amount,
		Note:   req.Note,
	}

	if err := h.Payments.Create(r.Context(), payment); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to record payment")
		return
	}

	writeJSON(w, http.StatusCreated, payment)
}

func (h *PaymentHandler) Subscribe(w http.ResponseWriter, r *http.Request) {
	idStr := middleware.GetUserID(r.Context())
	userID, _ := strconv.ParseInt(idStr, 10, 64)

	var req models.SubscribeRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	planType := req.PlanType
	if planType == "" {
		planType = "subscription"
	}

	if err := h.Influencers.Subscribe(r.Context(), userID, planType); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to subscribe")
		return
	}

	// Record the subscription payment
	payment := &models.Payment{
		Type:   "influencer_subscription",
		UserID: userID,
		Gross:  1499,
		Amount: 1499,
		Note:   "Creator Pro monthly subscription",
	}
	_ = h.Payments.Create(r.Context(), payment)

	writeJSON(w, http.StatusOK, map[string]string{"status": "subscribed", "plan": "pro"})
}
