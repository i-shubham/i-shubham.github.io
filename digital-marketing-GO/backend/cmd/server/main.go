package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	chimw "github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"github.com/smallick/plugg-backend/internal/config"
	"github.com/smallick/plugg-backend/internal/database"
	"github.com/smallick/plugg-backend/internal/handlers"
	"github.com/smallick/plugg-backend/internal/middleware"
	"github.com/smallick/plugg-backend/internal/repository"
)

func main() {
	cfg := config.Load()

	pool, err := database.Connect(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("DB connection failed: %v", err)
	}
	defer pool.Close()
	log.Println("Connected to PostgreSQL")

	// Repositories
	userRepo := &repository.UserRepo{DB: pool}
	influencerRepo := &repository.InfluencerRepo{DB: pool}
	brandRepo := &repository.BrandRepo{DB: pool}
	productRepo := &repository.ProductRepo{DB: pool}
	bidRepo := &repository.BidRepo{DB: pool}
	conceptRepo := &repository.ConceptRepo{DB: pool}
	paymentRepo := &repository.PaymentRepo{DB: pool}

	// Handlers
	authH := &handlers.AuthHandler{
		Users: userRepo, Influencers: influencerRepo, Brands: brandRepo,
		JWTSecret: cfg.JWTSecret,
	}
	userH := &handlers.UserHandler{Users: userRepo, Influencers: influencerRepo, Brands: brandRepo}
	productH := &handlers.ProductHandler{Products: productRepo}
	bidH := &handlers.BidHandler{Bids: bidRepo, Products: productRepo, Concepts: conceptRepo}
	influencerH := &handlers.InfluencerHandler{Influencers: influencerRepo, Users: userRepo}
	paymentH := &handlers.PaymentHandler{Payments: paymentRepo, Influencers: influencerRepo}
	adminH := &handlers.AdminHandler{Payments: paymentRepo}

	// Router
	r := chi.NewRouter()
	r.Use(chimw.Logger)
	r.Use(chimw.Recoverer)
	r.Use(chimw.RealIP)
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"*"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: false,
		MaxAge:           300,
	}))

	// Stats handler (public, no auth)
	statsH := &handlers.StatsHandler{DB: pool}

	// Public API routes
	r.Route("/api", func(r chi.Router) {
		r.Post("/auth/register", authH.Register)
		r.Post("/auth/login", authH.Login)
		r.Get("/stats", statsH.PublicStats)

		// Public read endpoints (marketplace/directory browsing)
		r.Get("/products", productH.List)
		r.Get("/products/{id}", productH.GetByID)
		r.Get("/influencers", influencerH.List)

		// Protected routes
		r.Group(func(r chi.Router) {
			r.Use(middleware.JWTAuth(cfg.JWTSecret))

			r.Get("/me", userH.Me)

			r.Post("/products", productH.Create)

			r.Get("/products/{id}/bids", bidH.ListByProduct)
			r.Post("/products/{id}/bids", bidH.Place)

			r.Patch("/bids/{id}", bidH.UpdateStatus)
			r.Post("/bids/{id}/concept", bidH.ShareConcept)
			r.Get("/bids/{id}/concept", bidH.GetConcept)

			r.Post("/influencers/connect", influencerH.ConnectSocial)
			r.Post("/influencers/sync", influencerH.SyncStats)

			r.Post("/payments", paymentH.RecordPayment)
			r.Post("/subscriptions", paymentH.Subscribe)

			r.Group(func(r chi.Router) {
				r.Use(middleware.RequireRole("admin"))
				r.Get("/admin/revenue", adminH.Revenue)
			})
		})
	})

	// Serve static frontend files with no-cache for dev
	fs := http.FileServer(http.Dir(cfg.FrontendDir))
	r.Handle("/*", http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
		w.Header().Set("Pragma", "no-cache")
		w.Header().Set("Expires", "0")
		fs.ServeHTTP(w, req)
	}))

	addr := fmt.Sprintf(":%s", cfg.Port)
	log.Printf("Plugg server starting on http://localhost%s", addr)
	log.Fatal(http.ListenAndServe(addr, r))
}
