package handlers

import (
	"math"
	"net/http"
	"strconv"

	"github.com/smallick/plugg-backend/internal/middleware"
	"github.com/smallick/plugg-backend/internal/models"
	"github.com/smallick/plugg-backend/internal/repository"
)

type InfluencerHandler struct {
	Influencers *repository.InfluencerRepo
	Users       *repository.UserRepo
}

func (h *InfluencerHandler) List(w http.ResponseWriter, r *http.Request) {
	profiles, err := h.Influencers.List(r.Context())
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to list influencers")
		return
	}
	if profiles == nil {
		profiles = []models.InfluencerProfile{}
	}

	type influencerWithName struct {
		models.InfluencerProfile
		Name string `json:"name"`
	}

	var result []influencerWithName
	for _, p := range profiles {
		user, _ := h.Users.GetByID(r.Context(), p.UserID)
		name := ""
		if user != nil {
			name = user.Name
		}
		result = append(result, influencerWithName{InfluencerProfile: p, Name: name})
	}

	writeJSON(w, http.StatusOK, result)
}

func (h *InfluencerHandler) ConnectSocial(w http.ResponseWriter, r *http.Request) {
	idStr := middleware.GetUserID(r.Context())
	userID, _ := strconv.ParseInt(idStr, 10, 64)

	var req models.ConnectSocialRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	// Get existing profile to preserve non-updated URL
	profile, err := h.Influencers.GetByUserID(r.Context(), userID)
	if err != nil {
		writeError(w, http.StatusNotFound, "profile not found")
		return
	}

	instaURL := profile.InstaURL
	ytURL := profile.YtURL
	if req.InstaURL != "" {
		instaURL = req.InstaURL
	}
	if req.YtURL != "" {
		ytURL = req.YtURL
	}

	if err := h.Influencers.UpdateSocial(r.Context(), userID, instaURL, ytURL); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to update social links")
		return
	}

	// Auto-sync stats after connecting
	instaFollowers, instaTopReel := deriveInstaStats(instaURL)
	ytSubs, ytTopViews := deriveYTStats(ytURL)
	engagement := 3.0 + float64(strHash(instaURL+ytURL)%50)/10.0
	_ = h.Influencers.UpdateStats(r.Context(), userID, instaFollowers, instaTopReel, ytSubs, ytTopViews, engagement)

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"status":         "connected",
		"instaFollowers": instaFollowers,
		"instaTopReel":   instaTopReel,
		"ytSubscribers":  ytSubs,
		"ytTopViews":     ytTopViews,
		"engagement":     engagement,
	})
}

func (h *InfluencerHandler) SyncStats(w http.ResponseWriter, r *http.Request) {
	idStr := middleware.GetUserID(r.Context())
	userID, _ := strconv.ParseInt(idStr, 10, 64)

	profile, err := h.Influencers.GetByUserID(r.Context(), userID)
	if err != nil {
		writeError(w, http.StatusNotFound, "profile not found")
		return
	}

	// Demo: derive stats deterministically from URLs (same logic as frontend seed)
	instaFollowers, instaTopReel := deriveInstaStats(profile.InstaURL)
	ytSubs, ytTopViews := deriveYTStats(profile.YtURL)
	engagement := 3.0 + float64(strHash(profile.InstaURL+profile.YtURL)%50)/10.0

	if err := h.Influencers.UpdateStats(r.Context(), userID, instaFollowers, instaTopReel, ytSubs, ytTopViews, engagement); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to sync stats")
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"instaFollowers": instaFollowers,
		"instaTopReel":   instaTopReel,
		"ytSubscribers":  ytSubs,
		"ytTopViews":     ytTopViews,
		"engagement":     engagement,
	})
}

func strHash(s string) int {
	h := 2166136261
	for _, c := range s {
		h ^= int(c)
		h *= 16777619
	}
	return int(math.Abs(float64(h)))
}

func deriveInstaStats(url string) (followers, topReel int) {
	if url == "" {
		return 0, 0
	}
	h := strHash(url)
	followers = 50000 + (h % 950000)
	topReel = 100000 + (h % 5000000)
	return
}

func deriveYTStats(url string) (subs, topViews int) {
	if url == "" {
		return 0, 0
	}
	h := strHash(url)
	subs = 10000 + (h % 490000)
	topViews = 50000 + (h % 3000000)
	return
}
