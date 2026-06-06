package handlers

import (
	"net/http"
	"strconv"

	"github.com/smallick/plugg-backend/internal/middleware"
	"github.com/smallick/plugg-backend/internal/models"
	"github.com/smallick/plugg-backend/internal/repository"
)

type BidHandler struct {
	Bids     *repository.BidRepo
	Products *repository.ProductRepo
	Concepts *repository.ConceptRepo
}

func (h *BidHandler) ListByProduct(w http.ResponseWriter, r *http.Request) {
	productID, err := urlParamInt64(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid product id")
		return
	}

	bids, err := h.Bids.ListByProduct(r.Context(), productID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to list bids")
		return
	}
	if bids == nil {
		bids = []models.Bid{}
	}
	writeJSON(w, http.StatusOK, bids)
}

func (h *BidHandler) Place(w http.ResponseWriter, r *http.Request) {
	productID, err := urlParamInt64(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid product id")
		return
	}

	idStr := middleware.GetUserID(r.Context())
	userID, _ := strconv.ParseInt(idStr, 10, 64)

	exists, _ := h.Bids.ExistsByInfluencerAndProduct(r.Context(), userID, productID)
	if exists {
		writeError(w, http.StatusConflict, "you already placed a bid on this campaign")
		return
	}

	var req models.PlaceBidRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	bid := &models.Bid{
		ProductID:        productID,
		InfluencerUserID: userID,
		Amount:           req.Amount,
		Message:          req.Message,
	}

	if err := h.Bids.Create(r.Context(), bid); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to place bid")
		return
	}

	writeJSON(w, http.StatusCreated, bid)
}

func (h *BidHandler) UpdateStatus(w http.ResponseWriter, r *http.Request) {
	bidID, err := urlParamInt64(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid bid id")
		return
	}

	var req models.UpdateBidRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if req.Status != "approved" && req.Status != "rejected" {
		writeError(w, http.StatusBadRequest, "status must be 'approved' or 'rejected'")
		return
	}

	bid, err := h.Bids.GetByID(r.Context(), bidID)
	if err != nil {
		writeError(w, http.StatusNotFound, "bid not found")
		return
	}

	if err := h.Bids.UpdateStatus(r.Context(), bidID, req.Status); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to update bid")
		return
	}

	if req.Status == "approved" {
		_ = h.Bids.RejectOthers(r.Context(), bid.ProductID, bidID)
		_ = h.Products.UpdateStatus(r.Context(), bid.ProductID, "in_progress")
	}

	writeJSON(w, http.StatusOK, map[string]string{"status": req.Status})
}

func (h *BidHandler) ShareConcept(w http.ResponseWriter, r *http.Request) {
	bidID, err := urlParamInt64(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid bid id")
		return
	}

	idStr := middleware.GetUserID(r.Context())
	userID, _ := strconv.ParseInt(idStr, 10, 64)

	bid, err := h.Bids.GetByID(r.Context(), bidID)
	if err != nil {
		writeError(w, http.StatusNotFound, "bid not found")
		return
	}

	var req models.ShareConceptRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	concept := &models.Concept{
		BidID:            bidID,
		ProductID:        bid.ProductID,
		BrandUserID:      userID,
		InfluencerUserID: bid.InfluencerUserID,
		Concept:          req.Concept,
		Script:           req.Script,
		Deliverables:     req.Deliverables,
		Deadline:         req.Deadline,
	}

	if err := h.Concepts.Create(r.Context(), concept); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to share concept")
		return
	}

	writeJSON(w, http.StatusCreated, concept)
}

func (h *BidHandler) GetConcept(w http.ResponseWriter, r *http.Request) {
	bidID, err := urlParamInt64(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid bid id")
		return
	}

	concept, err := h.Concepts.GetByBidID(r.Context(), bidID)
	if err != nil {
		writeError(w, http.StatusNotFound, "concept not found")
		return
	}

	writeJSON(w, http.StatusOK, concept)
}
