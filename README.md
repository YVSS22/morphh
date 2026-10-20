# Morphh

Transforme un personnage (dessin animé, illustration, photo…) en **version photoréaliste**, à l'identique.

Frontend épuré (bento grid, style Apple) + backend minimal en Python. Génération via **Gemini Nano Banana** (image → image, préserve l'identité, sortie 4K).

## Lancer

```bash
python3 server.py     # puis ouvrir http://localhost:8649
```

Nécessite `GEMINI_API_KEY` (facturation Gemini activée) dans `/root/.hermes/profiles/jorvas/.env`.

## Structure

- `server.py` — backend, `POST /api/photoreal` (image base64 → image photoréaliste)
- `index.html` / `style.css` / `app.js` — frontend (bento + design Apple)
