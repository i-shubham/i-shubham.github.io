package models

import "time"

type User struct {
	ID           int64     `json:"id"`
	Role         string    `json:"role"`
	Name         string    `json:"name"`
	Email        string    `json:"email"`
	PasswordHash string    `json:"-"`
	CreatedAt    time.Time `json:"createdAt"`
}

type InfluencerProfile struct {
	UserID          int64      `json:"userId"`
	Handle          string     `json:"handle"`
	Niche           string     `json:"niche"`
	Bio             string     `json:"bio"`
	Location        string     `json:"location"`
	Avatar          string     `json:"avatar"`
	InstaURL        string     `json:"instaUrl"`
	YtURL           string     `json:"ytUrl"`
	LastSynced      *time.Time `json:"lastSynced"`
	InstaFollowers  int        `json:"instaFollowers"`
	InstaTopReel    int        `json:"instaTopReel"`
	YtSubscribers   int        `json:"ytSubscribers"`
	YtTopViews      int        `json:"ytTopViews"`
	Engagement      float64    `json:"engagement"`
	TrialStart      time.Time  `json:"trialStart"`
	Plan            string     `json:"plan"`
	PlanType        string     `json:"planType"`
	SubscribedUntil *time.Time `json:"subscribedUntil"`
}

type BrandProfile struct {
	UserID  int64  `json:"userId"`
	Company string `json:"company"`
	Industry string `json:"industry"`
	Website string `json:"website"`
	About   string `json:"about"`
	Logo    string `json:"logo"`
}

type Product struct {
	ID           int64     `json:"id"`
	BrandUserID  int64     `json:"brandUserId"`
	Title        string    `json:"title"`
	Description  string    `json:"description"`
	Category     string    `json:"category"`
	Budget       float64   `json:"budget"`
	Deadline     string    `json:"deadline"`
	Deliverables string    `json:"deliverables"`
	Status       string    `json:"status"`
	CreatedAt    time.Time `json:"createdAt"`
	BrandName    string    `json:"brandName,omitempty"`
	BrandLogo    string    `json:"brandLogo,omitempty"`
}

type Bid struct {
	ID               int64     `json:"id"`
	ProductID        int64     `json:"productId"`
	InfluencerUserID int64     `json:"influencerUserId"`
	Amount           float64   `json:"amount"`
	Message          string    `json:"message"`
	Status           string    `json:"status"`
	CreatedAt        time.Time `json:"createdAt"`
	InfluencerName   string    `json:"influencerName,omitempty"`
	InfluencerHandle string    `json:"influencerHandle,omitempty"`
	InfluencerAvatar string    `json:"influencerAvatar,omitempty"`
}

type Concept struct {
	ID               int64     `json:"id"`
	BidID            int64     `json:"bidId"`
	ProductID        int64     `json:"productId"`
	BrandUserID      int64     `json:"brandUserId"`
	InfluencerUserID int64     `json:"influencerUserId"`
	Concept          string    `json:"concept"`
	Script           string    `json:"script"`
	Deliverables     string    `json:"deliverables"`
	Deadline         string    `json:"deadline"`
	SharedAt         time.Time `json:"sharedAt"`
}

type Payment struct {
	ID        int64     `json:"id"`
	Type      string    `json:"type"`
	UserID    int64     `json:"userId"`
	RefID     int64     `json:"refId"`
	Gross     float64   `json:"gross"`
	Amount    float64   `json:"amount"`
	Status    string    `json:"status"`
	Note      string    `json:"note"`
	CreatedAt time.Time `json:"createdAt"`
}

// JSON request/response types

type RegisterRequest struct {
	Name     string `json:"name"`
	Email    string `json:"email"`
	Password string `json:"password"`
	Role     string `json:"role"`
	// Influencer fields
	Handle   string `json:"handle,omitempty"`
	Niche    string `json:"niche,omitempty"`
	InstaURL string `json:"instaUrl,omitempty"`
	YtURL    string `json:"ytUrl,omitempty"`
	// Brand fields
	Company  string `json:"company,omitempty"`
	Industry string `json:"industry,omitempty"`
	Website  string `json:"website,omitempty"`
}

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type LoginResponse struct {
	Token string `json:"token"`
	User  User   `json:"user"`
}

type CreateProductRequest struct {
	Title        string  `json:"title"`
	Description  string  `json:"description"`
	Category     string  `json:"category"`
	Budget       float64 `json:"budget"`
	Deadline     string  `json:"deadline"`
	Deliverables string  `json:"deliverables"`
}

type PlaceBidRequest struct {
	Amount  float64 `json:"amount"`
	Message string  `json:"message"`
}

type UpdateBidRequest struct {
	Status string `json:"status"`
}

type ShareConceptRequest struct {
	Concept      string `json:"concept"`
	Script       string `json:"script"`
	Deliverables string `json:"deliverables"`
	Deadline     string `json:"deadline"`
}

type ConnectSocialRequest struct {
	InstaURL string `json:"instaUrl"`
	YtURL    string `json:"ytUrl"`
}

type SubscribeRequest struct {
	PlanType string `json:"planType"`
}

type RecordPaymentRequest struct {
	Type   string  `json:"type"`
	RefID  int64   `json:"refId"`
	Gross  float64 `json:"gross"`
	Amount float64 `json:"amount"`
	Note   string  `json:"note"`
}

type AdminRevenue struct {
	BrandCommissions        float64 `json:"brandCommissions"`
	InfluencerSubscriptions float64 `json:"influencerSubscriptions"`
	InfluencerCommissions   float64 `json:"influencerCommissions"`
	TotalRevenue            float64 `json:"totalRevenue"`
	RecentPayments          []Payment `json:"recentPayments"`
}
