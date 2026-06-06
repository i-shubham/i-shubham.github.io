package handlers

import (
	"net/http"
	"strconv"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/smallick/plugg-backend/internal/models"
	"github.com/smallick/plugg-backend/internal/repository"
	"golang.org/x/crypto/bcrypt"
)

type AuthHandler struct {
	Users        *repository.UserRepo
	Influencers  *repository.InfluencerRepo
	Brands       *repository.BrandRepo
	JWTSecret    string
}

func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	var req models.RegisterRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if req.Name == "" || req.Email == "" || req.Password == "" || req.Role == "" {
		writeError(w, http.StatusBadRequest, "name, email, password, and role are required")
		return
	}
	if req.Role != "influencer" && req.Role != "brand" {
		writeError(w, http.StatusBadRequest, "role must be 'influencer' or 'brand'")
		return
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to hash password")
		return
	}

	user := &models.User{
		Role:         req.Role,
		Name:         req.Name,
		Email:        req.Email,
		PasswordHash: string(hash),
	}

	if err := h.Users.Create(r.Context(), user); err != nil {
		writeError(w, http.StatusConflict, "email already registered")
		return
	}

	if req.Role == "influencer" {
		profile := &models.InfluencerProfile{
			UserID:   user.ID,
			Handle:   req.Handle,
			Niche:    req.Niche,
			InstaURL: req.InstaURL,
			YtURL:    req.YtURL,
		}
		_ = h.Influencers.Create(r.Context(), profile)
	} else {
		profile := &models.BrandProfile{
			UserID:   user.ID,
			Company:  req.Company,
			Industry: req.Industry,
			Website:  req.Website,
		}
		_ = h.Brands.Create(r.Context(), profile)
	}

	token, _ := h.generateToken(user)
	writeJSON(w, http.StatusCreated, models.LoginResponse{Token: token, User: *user})
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	var req models.LoginRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	user, err := h.Users.GetByEmail(r.Context(), req.Email)
	if err != nil {
		writeError(w, http.StatusUnauthorized, "invalid email or password")
		return
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
		writeError(w, http.StatusUnauthorized, "invalid email or password")
		return
	}

	token, _ := h.generateToken(user)
	writeJSON(w, http.StatusOK, models.LoginResponse{Token: token, User: *user})
}

func (h *AuthHandler) generateToken(user *models.User) (string, error) {
	claims := jwt.MapClaims{
		"sub":  strconv.FormatInt(user.ID, 10),
		"role": user.Role,
		"name": user.Name,
		"exp":  time.Now().Add(72 * time.Hour).Unix(),
		"iat":  time.Now().Unix(),
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(h.JWTSecret))
}
