import os
from typing import Optional

try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None  # type: ignore

_supabase_client: Optional["Client"] = None


def get_supabase_client():
    """Create or return a cached Supabase client using environment variables.

    Required env vars:
      - SUPABASE_URL
      - SUPABASE_SERVICE_ROLE_KEY (preferred for server-side writes) or SUPABASE_ANON_KEY
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if create_client is None:
        raise RuntimeError("supabase package is not installed. Add 'supabase==2.4.3' to requirements.txt")

    supabase_url = os.getenv("SUPABASE_URL")
    # Accept multiple common env var names for convenience
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")  # allow generic SUPABASE_KEY if provided
        or os.getenv("SUPABASE_ANON_KEY")
    )

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) must be set"
        )

    _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client


