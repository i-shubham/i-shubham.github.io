package handlers

import (
	"net/http"
	"strconv"

	"github.com/smallick/plugg-backend/internal/middleware"
	"github.com/smallick/plugg-backend/internal/repository"
)

type UserHandler struct {
	Users       *repository.UserRepo
	Influencers *repository.InfluencerRepo
	Brands      *repository.BrandRepo
}

func (h *UserHandler) Me(w http.ResponseWriter, r *http.Request) {
	idStr := middleware.GetUserID(r.Context())
	id, err := strconv.ParseInt(idStr, 10, 64)
	if err != nil {
		writeError(w, http.StatusUnauthorized, "invalid user id in token")
		return
	}

	user, err := h.Users.GetByID(r.Context(), id)
	if err != nil {
		writeError(w, http.StatusNotFound, "user not found")
		return
	}

	role := middleware.GetUserRole(r.Context())
	response := map[string]interface{}{"user": user}

	if role == "influencer" {
		profile, _ := h.Influencers.GetByUserID(r.Context(), id)
		if profile != nil {
			response["profile"] = profile
		}
	} else if role == "brand" {
		profile, _ := h.Brands.GetByUserID(r.Context(), id)
		if profile != nil {
			response["profile"] = profile
		}
	}

	writeJSON(w, http.StatusOK, response)
}
