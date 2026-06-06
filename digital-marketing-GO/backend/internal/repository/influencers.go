package repository

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smallick/plugg-backend/internal/models"
)

type InfluencerRepo struct {
	DB *pgxpool.Pool
}

func (r *InfluencerRepo) Create(ctx context.Context, p *models.InfluencerProfile) error {
	_, err := r.DB.Exec(ctx,
		`INSERT INTO influencer_profiles
		 (user_id, handle, niche, bio, location, avatar, insta_url, yt_url, trial_start, plan, plan_type)
		 VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)`,
		p.UserID, p.Handle, p.Niche, p.Bio, p.Location, p.Avatar,
		p.InstaURL, p.YtURL, time.Now(), "trial", "commission",
	)
	return err
}

func (r *InfluencerRepo) GetByUserID(ctx context.Context, userID int64) (*models.InfluencerProfile, error) {
	p := &models.InfluencerProfile{}
	err := r.DB.QueryRow(ctx,
		`SELECT user_id, handle, niche, bio, location, avatar,
		        insta_url, yt_url, last_synced,
		        insta_followers, insta_top_reel, yt_subscribers, yt_top_views, engagement,
		        trial_start, plan, plan_type, subscribed_until
		 FROM influencer_profiles WHERE user_id = $1`, userID,
	).Scan(
		&p.UserID, &p.Handle, &p.Niche, &p.Bio, &p.Location, &p.Avatar,
		&p.InstaURL, &p.YtURL, &p.LastSynced,
		&p.InstaFollowers, &p.InstaTopReel, &p.YtSubscribers, &p.YtTopViews, &p.Engagement,
		&p.TrialStart, &p.Plan, &p.PlanType, &p.SubscribedUntil,
	)
	if err != nil {
		return nil, err
	}
	return p, nil
}

func (r *InfluencerRepo) List(ctx context.Context) ([]models.InfluencerProfile, error) {
	rows, err := r.DB.Query(ctx,
		`SELECT user_id, handle, niche, bio, location, avatar,
		        insta_url, yt_url, last_synced,
		        insta_followers, insta_top_reel, yt_subscribers, yt_top_views, engagement,
		        trial_start, plan, plan_type, subscribed_until
		 FROM influencer_profiles ORDER BY insta_followers DESC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var list []models.InfluencerProfile
	for rows.Next() {
		var p models.InfluencerProfile
		if err := rows.Scan(
			&p.UserID, &p.Handle, &p.Niche, &p.Bio, &p.Location, &p.Avatar,
			&p.InstaURL, &p.YtURL, &p.LastSynced,
			&p.InstaFollowers, &p.InstaTopReel, &p.YtSubscribers, &p.YtTopViews, &p.Engagement,
			&p.TrialStart, &p.Plan, &p.PlanType, &p.SubscribedUntil,
		); err != nil {
			return nil, err
		}
		list = append(list, p)
	}
	return list, nil
}

func (r *InfluencerRepo) UpdateSocial(ctx context.Context, userID int64, instaURL, ytURL string) error {
	_, err := r.DB.Exec(ctx,
		`UPDATE influencer_profiles SET insta_url=$1, yt_url=$2 WHERE user_id=$3`,
		instaURL, ytURL, userID,
	)
	return err
}

func (r *InfluencerRepo) UpdateStats(ctx context.Context, userID int64, instaFollowers, instaTopReel, ytSubs, ytTopViews int, engagement float64) error {
	_, err := r.DB.Exec(ctx,
		`UPDATE influencer_profiles
		 SET insta_followers=$1, insta_top_reel=$2, yt_subscribers=$3, yt_top_views=$4, engagement=$5, last_synced=$6
		 WHERE user_id=$7`,
		instaFollowers, instaTopReel, ytSubs, ytTopViews, engagement, time.Now(), userID,
	)
	return err
}

func (r *InfluencerRepo) Subscribe(ctx context.Context, userID int64, planType string) error {
	until := time.Now().AddDate(0, 1, 0)
	_, err := r.DB.Exec(ctx,
		`UPDATE influencer_profiles SET plan='pro', plan_type=$1, subscribed_until=$2 WHERE user_id=$3`,
		planType, until, userID,
	)
	return err
}
