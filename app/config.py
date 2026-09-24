"""
Configuration for Freelancer LeadTools.

Loads settings from environment variables with sensible defaults.

Domain Configuration:
- BASE_DOMAIN: Primary domain (e.g., osfreelance.com)
- Both .com and .io should route to the same backend via DNS/CDN
- Subdomains: api.freelancerleadtools, app.freelancegrowth, app.freelancedealflow
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ======================================================================
    # Domain Configuration
    # ======================================================================
    base_domain: str = "osfreelance.com"
    
    # API subdomains
    leadtools_subdomain: str = "api.freelancerleadtools"
    growth_subdomain: str = "api.freelancegrowth"
    dealflow_subdomain: str = "api.freelancedealflow"
    
    # Frontend subdomains (for CTAs)
    growth_frontend_subdomain: str = "app.freelancegrowth"
    dealflow_frontend_subdomain: str = "app.freelancedealflow"

    # ======================================================================
    # Application Settings
    # ======================================================================
    app_name: str = "Freelancer LeadTools"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production
    # Optional same-origin browser gateway. Tokens stay in private Redis.
    web_public_origin: str = "http://127.0.0.1:8091"
    identity_api_url: str = ""
    workspace_dealflow_url: str = ""

    # ======================================================================
    # Server Settings
    # ======================================================================
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False  # Auto-reload for development

    # ======================================================================
    # Product URLs (for CTAs) - Constructed from domain config
    # ======================================================================
    # These are auto-generated from subdomain + base_domain
    # Override directly if needed
    
    # Individual Freelancer Product
    freelance_growth_url: Optional[str] = None  # Auto-generated if not set
    freelance_growth_signup: str = "/signup"

    # Agency Product
    freelancer_dealflow_url: Optional[str] = None  # Auto-generated if not set
    freelancer_dealflow_signup: str = "/signup"

    # ======================================================================
    # Lead Capture Settings
    # ======================================================================
    enable_lead_capture: bool = True
    lead_capture_provider: str = "convertkit"  # convertkit, mailchimp, custom
    convertkit_api_key: str = ""
    convertkit_form_id: str = ""
    mailchimp_api_key: str = ""
    mailchimp_audience_id: str = ""

    # ======================================================================
    # Analytics Settings
    # ======================================================================
    analytics_provider: str = "plausible"  # plausible, google, umami
    plausible_domain: str = ""
    google_analytics_id: str = ""
    umami_website_id: str = ""
    enable_analytics: bool = True

    # ======================================================================
    # Email Settings (for sending results)
    # ======================================================================
    email_from: str = "noreply@leadtools.osfreelance.com"
    email_from_name: str = "Freelancer LeadTools"
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_use_tls: bool = True

    # ======================================================================
    # Rate Limiting
    # ======================================================================
    rate_limit_requests: int = 100  # requests per window
    rate_limit_window_seconds: int = 60  # window size in seconds
    rate_limit_enabled: bool = True
    rate_limit_whitelist: list[str] = []  # IPs to bypass rate limiting

    # ======================================================================
    # CORS Settings
    # ======================================================================
    # Both .com and .io should be allowed
    cors_allow_origins: list[str] = []
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # ======================================================================
    # Logging Settings
    # ======================================================================
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "json"  # json, text

    # ======================================================================
    # Security Settings
    # ======================================================================
    api_key_header: str = "X-API-Key"
    api_keys: list[str] = []  # List of valid API keys for protected endpoints
    lead_unsubscribe_secret: str = ""

    # ======================================================================
    # Database (for lead storage - optional, uses memory by default)
    # ======================================================================
    database_url: str = ""  # Empty = use in-memory storage

    # ======================================================================
    # Cache Settings (Redis)
    # ======================================================================
    redis_url: str = ""  # Empty = no caching
    cache_ttl_seconds: int = 3600

    # Versioned external reference data, refreshed only by an explicit job.
    reference_data_countries: str = "KEN,USA,GBR"
    reference_data_max_age_days: int = 500
    reference_data_timeout_seconds: float = 20.0

    # ======================================================================
    # Feature Flags
    # ======================================================================
    enable_burnout_calculator: bool = True
    enable_skill_gap_calculator: bool = True
    enable_portfolio_calculator: bool = True
    enable_client_fit_calculator: bool = True
    enable_scope_creep_calculator: bool = True
    enable_hourly_rate_calculator: bool = True
    enable_freelance_vs_fulltime_calculator: bool = True
    enable_agency_profit_calculator: bool = True
    enable_utilization_calculator: bool = True
    enable_client_ltv_calculator: bool = True
    enable_proposal_win_rate_calculator: bool = True
    enable_cash_flow_calculator: bool = True
    enable_break_even_calculator: bool = True
    enable_rate_ppp_calculator: bool = True
    enable_tax_estimator_calculator: bool = True
    enable_retirement_calculator: bool = True
    enable_time_value_calculator: bool = True

    # ======================================================================
    # Computed Properties
    # ======================================================================
    
    @property
    def growth_api_url(self) -> str:
        """Get the Growth API URL."""
        return f"https://{self.growth_subdomain}.{self.base_domain}"
    
    @property
    def dealflow_api_url(self) -> str:
        """Get the DealFlow API URL."""
        return f"https://{self.dealflow_subdomain}.{self.base_domain}"
    
    @property
    def leadtools_api_url(self) -> str:
        """Get the LeadTools API URL."""
        return f"https://{self.leadtools_subdomain}.{self.base_domain}"
    
    @property
    def effective_growth_url(self) -> str:
        """Get the effective Growth frontend URL."""
        if self.freelance_growth_url:
            return self.freelance_growth_url
        return f"https://{self.growth_frontend_subdomain}.{self.base_domain}"
    
    @property
    def effective_dealflow_url(self) -> str:
        """Get the effective DealFlow frontend URL."""
        if self.freelancer_dealflow_url:
            return self.freelancer_dealflow_url
        return f"https://{self.dealflow_frontend_subdomain}.{self.base_domain}"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def get_product_url(self, product: str) -> str:
        """Get the base URL for a product."""
        if product == "freelance-growth":
            return self.effective_growth_url
        elif product == "freelancer-dealflow":
            return self.effective_dealflow_url
        else:
            raise ValueError(f"Unknown product: {product}")

    def get_signup_url(self, product: str, source: str) -> str:
        """
        Generate signup URL with UTM tracking.

        Args:
            product: Either 'freelance-growth' or 'freelancer-dealflow'
            source: The calculator source (e.g., 'burnout-calculator')
        """
        base_url = self.get_product_url(product)
        if product == "freelance-growth":
            signup_path = self.freelance_growth_signup
        else:
            signup_path = self.freelancer_dealflow_signup

        # Build URL with UTM parameters
        return (
            f"{base_url}{signup_path}"
            f"?utm_source=leadtools"
            f"&utm_medium=calculator"
            f"&utm_campaign={source}"
        )

    def get_default_cors_origins(self) -> list[str]:
        """Get default CORS origins for the current domain configuration."""
        return [
            f"https://{self.leadtools_subdomain}.{self.base_domain}",
            f"https://{self.leadtools_subdomain}.osfreelance.io",
            f"https://{self.growth_subdomain}.{self.base_domain}",
            f"https://{self.growth_subdomain}.osfreelance.io",
            f"https://{self.dealflow_subdomain}.{self.base_domain}",
            f"https://{self.dealflow_subdomain}.osfreelance.io",
            f"https://{self.growth_frontend_subdomain}.{self.base_domain}",
            f"https://{self.growth_frontend_subdomain}.osfreelance.io",
            f"https://{self.dealflow_frontend_subdomain}.{self.base_domain}",
            f"https://{self.dealflow_frontend_subdomain}.osfreelance.io",
        ]

    def model_post_init(self, __context):
        """Post-initialization to set defaults."""
        # Set default CORS origins if not provided
        if not self.cors_allow_origins:
            self.cors_allow_origins = self.get_default_cors_origins()
        
        # Update email from with domain
        if self.email_from == "noreply@leadtools.osfreelance.com":
            self.email_from = f"noreply@leadtools.{self.base_domain}"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.is_production:
            missing = []
            if not self.database_url:
                missing.append("DATABASE_URL")
            if not self.redis_url:
                missing.append("REDIS_URL")
            if not self.api_keys:
                missing.append("API_KEYS")
            if len(self.lead_unsubscribe_secret) < 32:
                missing.append("LEAD_UNSUBSCRIBE_SECRET (minimum 32 characters)")
            if missing:
                raise ValueError("Missing production settings: " + ", ".join(missing))
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to avoid reloading settings on every request.
    Call get_settings.cache_clear() to invalidate cache.
    """
    return Settings()


# Convenience function for accessing settings
settings = get_settings()
