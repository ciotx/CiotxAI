package api

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"

	"github.com/ciotx/cli/internal/config"
)

type UserResponse struct {
	ID            string `json:"id"`
	Email         string `json:"email"`
	Name          string `json:"name"`
	Plan          string `json:"plan"`
	PlanStatus    string `json:"plan_status"`
	EmailVerified bool   `json:"email_verified"`
}

func GetMe(cfg *config.Config) (*UserResponse, error) {
	req, err := http.NewRequest("GET", cfg.APIURL+"/v1/auth/me", nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+cfg.AccessToken)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch user info: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (%d): %s", resp.StatusCode, strings.TrimSpace(string(body)))
	}

	var user UserResponse
	if err := json.NewDecoder(resp.Body).Decode(&user); err != nil {
		return nil, fmt.Errorf("failed to parse user response: %w", err)
	}

	return &user, nil
}

func RefreshToken(cfg *config.Config) error {
	if cfg.RefreshToken == "" {
		return fmt.Errorf("no refresh token available")
	}

	body := fmt.Sprintf(`{"refresh_token":"%s"}`, cfg.RefreshToken)
	resp, err := http.Post(
		cfg.APIURL+"/v1/auth/refresh",
		"application/json",
		strings.NewReader(body),
	)
	if err != nil {
		return fmt.Errorf("failed to refresh token: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		cfg.ClearAuth()
		config.Save(cfg)
		return fmt.Errorf("token refresh failed — please log in again")
	}

	var result struct {
		AccessToken  string `json:"access_token"`
		RefreshToken string `json:"refresh_token"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return fmt.Errorf("failed to parse refresh response: %w", err)
	}

	cfg.AccessToken = result.AccessToken
	cfg.RefreshToken = result.RefreshToken
	config.Save(cfg)

	return nil
}
