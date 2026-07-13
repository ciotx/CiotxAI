package auth

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

type CliInitResponse struct {
	DeviceCode      string `json:"device_code"`
	UserCode        string `json:"user_code"`
	VerificationURI string `json:"verification_uri"`
	ExpiresIn       int    `json:"expires_in"`
}

type TokenResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
}

func generateCodeVerifier() (string, error) {
	bytes := make([]byte, 32)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(bytes), nil
}

func generateCodeChallenge(verifier string) string {
	hash := sha256.Sum256([]byte(verifier))
	return base64.RawURLEncoding.EncodeToString(hash[:])
}

func InitPKCE(apiURL string) (*CliInitResponse, string, error) {
	verifier, err := generateCodeVerifier()
	if err != nil {
		return nil, "", fmt.Errorf("failed to generate code verifier: %w", err)
	}

	challenge := generateCodeChallenge(verifier)

	body := fmt.Sprintf(`{"code_challenge":"%s"}`, challenge)
	resp, err := http.Post(
		apiURL+"/v1/auth/cli/init",
		"application/json",
		strings.NewReader(body),
	)
	if err != nil {
		return nil, "", fmt.Errorf("failed to initiate PKCE: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, "", fmt.Errorf("PKCE init failed (%d): %s", resp.StatusCode, string(respBody))
	}

	var result CliInitResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, "", fmt.Errorf("failed to parse PKCE init response: %w", err)
	}

	return &result, verifier, nil
}

func PollForToken(apiURL, deviceCode, codeVerifier string, timeout time.Duration) (*TokenResponse, error) {
	deadline := time.Now().Add(timeout)
	interval := 2 * time.Second

	for time.Now().Before(deadline) {
		body := fmt.Sprintf(
			`{"device_code":"%s","code_verifier":"%s"}`,
			deviceCode, codeVerifier,
		)
		resp, err := http.Post(
			apiURL+"/v1/auth/cli/token",
			"application/json",
			strings.NewReader(body),
		)
		if err != nil {
			time.Sleep(interval)
			continue
		}

		if resp.StatusCode == 200 {
			var token TokenResponse
			if err := json.NewDecoder(resp.Body).Decode(&token); err != nil {
				resp.Body.Close()
				return nil, fmt.Errorf("failed to parse token response: %w", err)
			}
			resp.Body.Close()
			return &token, nil
		}

		resp.Body.Close()

		// If 400, user hasn't confirmed yet — keep polling
		if resp.StatusCode == 400 {
			time.Sleep(interval)
			continue
		}

		// Other errors
		return nil, fmt.Errorf("token request failed with status %d", resp.StatusCode)
	}

	return nil, fmt.Errorf("timed out waiting for authorization")
}
