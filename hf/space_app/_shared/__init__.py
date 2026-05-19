"""Production backend modules vendored at deploy time.

This directory is intentionally otherwise empty in source control. The
`hf-space.yml` workflow copies `backend/app/api/compatibility.py` and
`backend/app/api/marketplace.py` here before pushing to the Space, so
the demo serves byte-identical responses to production.

Vendoring at deploy time (instead of `pip install -e ../backend`)
keeps the published Space image self-contained: it has no awareness
of the backend's auth, db, or secret-vault dependencies.
"""
