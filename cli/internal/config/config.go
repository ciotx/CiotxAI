package config

import (
	"encoding/json"
	"os"
	"path/filepath"
)

// DefaultAPIURL and DefaultDashboardURL are set at compile time via ldflags:
//
//	go build -ldflags="-X 'github.com/ciotx/cli/internal/config.DefaultAPIURL=https://api.example.com'"
//
// Fall back to localhost for local dev builds.
var DefaultAPIURL = "http://localhost:8000"
var DefaultDashboardURL = "http://localhost:3000"

type Config struct {
	APIURL       string `json:"api_url"`
	DashboardURL string `json:"dashboard_url"`
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	UserID       string `json:"user_id,omitempty"`
	UserEmail    string `json:"user_email,omitempty"`
}

func configPath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	dir := filepath.Join(home, ".ciotx")
	if err := os.MkdirAll(dir, 0700); err != nil {
		return "", err
	}
	return filepath.Join(dir, "config.json"), nil
}

func Load() (*Config, error) {
	path, err := configPath()
	if err != nil {
		return nil, err
	}

	// Priority: env var > compiled default > hardcoded fallback
	defaultAPIURL := os.Getenv("CIOTX_API_URL")
	if defaultAPIURL == "" {
		defaultAPIURL = DefaultAPIURL
	}
	defaultDashboardURL := os.Getenv("CIOTX_DASHBOARD_URL")
	if defaultDashboardURL == "" {
		defaultDashboardURL = DefaultDashboardURL
	}

	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return &Config{APIURL: defaultAPIURL, DashboardURL: defaultDashboardURL}, nil
		}
		return nil, err
	}

	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}
	if cfg.APIURL == "" {
		cfg.APIURL = defaultAPIURL
	}
	if cfg.DashboardURL == "" {
		cfg.DashboardURL = defaultDashboardURL
	}
	return &cfg, nil
}

func Save(cfg *Config) error {
	path, err := configPath()
	if err != nil {
		return err
	}

	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(path, data, 0600)
}

func (c *Config) IsAuthenticated() bool {
	return c.AccessToken != ""
}

func (c *Config) ClearAuth() {
	c.AccessToken = ""
	c.RefreshToken = ""
	c.UserID = ""
	c.UserEmail = ""
}
