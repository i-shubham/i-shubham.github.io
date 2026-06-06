package handlers

import (
	"net/http"
	"strconv"

	"github.com/smallick/plugg-backend/internal/middleware"
	"github.com/smallick/plugg-backend/internal/models"
	"github.com/smallick/plugg-backend/internal/repository"
)

type ProductHandler struct {
	Products *repository.ProductRepo
}

func (h *ProductHandler) List(w http.ResponseWriter, r *http.Request) {
	products, err := h.Products.List(r.Context())
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to list products")
		return
	}
	if products == nil {
		products = []models.Product{}
	}
	writeJSON(w, http.StatusOK, products)
}

func (h *ProductHandler) Create(w http.ResponseWriter, r *http.Request) {
	idStr := middleware.GetUserID(r.Context())
	userID, _ := strconv.ParseInt(idStr, 10, 64)

	var req models.CreateProductRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if req.Title == "" || req.Budget <= 0 {
		writeError(w, http.StatusBadRequest, "title and budget are required")
		return
	}

	product := &models.Product{
		BrandUserID:  userID,
		Title:        req.Title,
		Description:  req.Description,
		Category:     req.Category,
		Budget:       req.Budget,
		Deadline:     req.Deadline,
		Deliverables: req.Deliverables,
	}

	if err := h.Products.Create(r.Context(), product); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to create product")
		return
	}

	writeJSON(w, http.StatusCreated, product)
}

func (h *ProductHandler) GetByID(w http.ResponseWriter, r *http.Request) {
	id, err := urlParamInt64(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid product id")
		return
	}

	product, err := h.Products.GetByID(r.Context(), id)
	if err != nil {
		writeError(w, http.StatusNotFound, "product not found")
		return
	}

	writeJSON(w, http.StatusOK, product)
}
