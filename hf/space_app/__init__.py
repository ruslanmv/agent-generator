"""Slim FastAPI demo backend for the Hugging Face Space.

The demo is a thin wrapper around the published `agent-generator`
package and a small set of production backend modules that the
deploy workflow vendors into `_shared/`. There is no application
state beyond the in-memory project store maintained by
`routes.generate`, so a Space restart is harmless.

Module layout:

    space_app/
        main.py              FastAPI app + SPA static mount
        config.py            Environment config (Pydantic-Settings)
        routes/
            plan.py          POST /api/plan
            build.py         POST /api/build
            generate.py      POST /api/generate, GET /api/projects/...
            compatibility.py thin re-export of the production router
            marketplace.py   in-memory fixture, mirrors prod shape
            health.py        GET /health, GET /api/health
        _shared/             populated by CI from backend/app/api/
"""

__version__ = "1.0.0"
