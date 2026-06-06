package main

import (
	"context"
	"log"

	"github.com/smallick/plugg-backend/internal/config"
	"github.com/smallick/plugg-backend/internal/database"
	"github.com/smallick/plugg-backend/internal/models"
	"github.com/smallick/plugg-backend/internal/repository"
	"golang.org/x/crypto/bcrypt"
)

func main() {
	cfg := config.Load()
	pool, err := database.Connect(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("DB connection failed: %v", err)
	}
	defer pool.Close()

	ctx := context.Background()

	userRepo := &repository.UserRepo{DB: pool}
	influencerRepo := &repository.InfluencerRepo{DB: pool}
	brandRepo := &repository.BrandRepo{DB: pool}
	productRepo := &repository.ProductRepo{DB: pool}
	bidRepo := &repository.BidRepo{DB: pool}

	hash := func(pw string) string {
		h, _ := bcrypt.GenerateFromPassword([]byte(pw), bcrypt.DefaultCost)
		return string(h)
	}

	// --- Admin ---
	admin := &models.User{Role: "admin", Name: "Plugg Admin", Email: "admin@plugg.io", PasswordHash: hash("admin123")}
	if err := userRepo.Create(ctx, admin); err != nil {
		log.Printf("Admin may already exist: %v", err)
	} else {
		log.Printf("Created admin: id=%d email=%s", admin.ID, admin.Email)
	}

	// --- Influencers ---
	influencers := []struct {
		name, email, handle, niche, instaURL, ytURL, avatar string
	}{
		{"Aarav Creates", "aaravcreates@demo.io", "aaravcreates", "Tech", "https://instagram.com/aaravcreates", "https://youtube.com/@aaravcreates", "img/influencers/inf-aarav.png"},
		{"Diya Fashions", "diyafashions@demo.io", "diyafashions", "Fashion", "https://instagram.com/diyafashions", "https://youtube.com/@diyafashion", "img/influencers/inf-diya.png"},
		{"Rohan Fitness", "rohanfit@demo.io", "rohanfit", "Fitness", "https://instagram.com/rohanfit", "", "img/influencers/inf-rohan.png"},
		{"Ishita Travels", "ishitatravels@demo.io", "ishitatravels", "Travel", "https://instagram.com/ishitatravels", "https://youtube.com/@ishitatravels", "img/influencers/inf-ishita.png"},
		{"Kabir Vlogs", "kabirvlogs@demo.io", "kabirvlogs", "Lifestyle", "https://instagram.com/kabirvlogs", "https://youtube.com/@kabirvlogs", "img/influencers/inf-kabir.png"},
	}

	for _, inf := range influencers {
		user := &models.User{Role: "influencer", Name: inf.name, Email: inf.email, PasswordHash: hash("demo123")}
		if err := userRepo.Create(ctx, user); err != nil {
			log.Printf("Influencer %s may already exist: %v", inf.email, err)
			continue
		}
		profile := &models.InfluencerProfile{
			UserID: user.ID, Handle: inf.handle, Niche: inf.niche,
			InstaURL: inf.instaURL, YtURL: inf.ytURL, Avatar: inf.avatar,
		}
		if err := influencerRepo.Create(ctx, profile); err != nil {
			log.Printf("  Profile create error: %v", err)
		}
		// Sync stats from URLs
		instaFollowers, instaTopReel := deriveInstaStats(inf.instaURL)
		ytSubs, ytTopViews := deriveYTStats(inf.ytURL)
		engagement := 3.0 + float64(strHash(inf.instaURL+inf.ytURL)%50)/10.0
		_ = influencerRepo.UpdateStats(ctx, user.ID, instaFollowers, instaTopReel, ytSubs, ytTopViews, engagement)
		log.Printf("Created influencer: id=%d %s (@%s)", user.ID, inf.name, inf.handle)
	}

	// --- Brands ---
	brands := []struct {
		name, email, company, industry, website, logo string
	}{
		{"Nimbus Audio", "nimbusaudio@demo.io", "Nimbus Audio", "Electronics", "https://nimbusaudio.com", "img/brands/brand-nimbus.png"},
		{"GreenLeaf Organics", "greenleaf@demo.io", "GreenLeaf Organics", "Health & Beauty", "https://greenleaforganics.in", "img/brands/brand-greenleaf.png"},
		{"Lumio Tech", "lumio@demo.io", "Lumio Tech", "Fashion", "https://lumio.co", "img/brands/brand-lumio.png"},
	}

	for _, br := range brands {
		user := &models.User{Role: "brand", Name: br.name, Email: br.email, PasswordHash: hash("demo123")}
		if err := userRepo.Create(ctx, user); err != nil {
			log.Printf("Brand %s may already exist: %v", br.email, err)
			continue
		}
		profile := &models.BrandProfile{
			UserID: user.ID, Company: br.company, Industry: br.industry,
			Website: br.website, Logo: br.logo,
		}
		if err := brandRepo.Create(ctx, profile); err != nil {
			log.Printf("  Brand profile error: %v", err)
		}
		log.Printf("Created brand: id=%d %s", user.ID, br.company)
	}

	// --- Products (from first two brands) ---
	// Get brand IDs
	nimbus, _ := userRepo.GetByEmail(ctx, "nimbusaudio@demo.io")
	greenleaf, _ := userRepo.GetByEmail(ctx, "greenleaf@demo.io")

	products := []struct {
		brandID                                      int64
		title, desc, category, deadline, deliverables string
		budget                                       float64
	}{
		{nimbus.ID, "Wireless Earbuds Launch", "Promote our new ANC earbuds with an unboxing + review reel", "Tech", "2025-02-28", "1 Reel (60s) + 3 Stories", 25000},
		{nimbus.ID, "Podcast Mic Campaign", "Showcase our USB-C podcast microphone for creators", "Tech", "2025-03-15", "1 YouTube video (8-12 min)", 40000},
		{greenleaf.ID, "Organic Skincare Range", "Feature our new turmeric face serum in a morning routine video", "Beauty", "2025-02-20", "1 Reel + 1 Story with swipe-up link", 18000},
		{greenleaf.ID, "Protein Bar Launch", "Taste-test & review our new vegan protein bars", "Food", "2025-03-01", "1 YouTube Short + 2 Stories", 12000},
	}

	for _, p := range products {
		product := &models.Product{
			BrandUserID: p.brandID, Title: p.title, Description: p.desc,
			Category: p.category, Budget: p.budget, Deadline: p.deadline,
			Deliverables: p.deliverables,
		}
		if err := productRepo.Create(ctx, product); err != nil {
			log.Printf("Product error: %v", err)
		} else {
			log.Printf("Created product: id=%d \"%s\"", product.ID, p.title)
		}
	}

	// --- A few demo bids ---
	aarav, _ := userRepo.GetByEmail(ctx, "aaravcreates@demo.io")
	diya, _ := userRepo.GetByEmail(ctx, "diyafashions@demo.io")

	demoBids := []struct {
		productID, infUserID int64
		amount               float64
		message              string
	}{
		{1, aarav.ID, 20000, "I'd love to review these earbuds! My audience is very tech-savvy."},
		{1, diya.ID, 22000, "I can create a lifestyle + unboxing aesthetic reel for this."},
		{3, diya.ID, 15000, "Skincare content is my forte — high engagement on beauty reels!"},
	}

	for _, b := range demoBids {
		bid := &models.Bid{ProductID: b.productID, InfluencerUserID: b.infUserID, Amount: b.amount, Message: b.message}
		if err := bidRepo.Create(ctx, bid); err != nil {
			log.Printf("Bid error: %v", err)
		} else {
			log.Printf("Created bid: id=%d on product %d by user %d", bid.ID, b.productID, b.infUserID)
		}
	}

	log.Println("Seed complete!")
}

// Same hash logic as frontend for consistent demo stats
func strHash(s string) int {
	h := 2166136261
	for _, c := range s {
		h ^= int(c)
		h *= 16777619
	}
	if h < 0 {
		h = -h
	}
	return h
}

func deriveInstaStats(url string) (int, int) {
	if url == "" {
		return 0, 0
	}
	h := strHash(url)
	return 50000 + (h % 950000), 100000 + (h % 5000000)
}

func deriveYTStats(url string) (int, int) {
	if url == "" {
		return 0, 0
	}
	h := strHash(url)
	return 10000 + (h % 490000), 50000 + (h % 3000000)
}
