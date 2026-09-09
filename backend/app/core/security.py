"""
Password hashing + JWT issuing/verification (FR-1.2, FR-1.3).

Implemented in Phase 1 alongside the auth module. Kept as a dedicated
core file (rather than inside modules/auth) because jobs/candidates
modules also depend on it for role guards, per SDD §5.
"""

# TODO(Phase 1): passlib bcrypt hashing helpers (hash_password, verify_password)
# TODO(Phase 1): JWT encode/decode helpers (create_access_token, create_refresh_token, decode_token)
