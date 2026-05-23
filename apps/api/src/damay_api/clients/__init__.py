"""External service clients (Supabase, Stellar, Twilio).

Each client wraps a single dependency, owns its own timeout/retry/breaker
policy, and exposes a small async surface to services/routers.
"""
