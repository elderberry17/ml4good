# Incident or Fiction?

A city game about AI safety. You are the mayor: each building of your city has two reports waiting,
one real incident from the [AI Incident Database](https://incidentdatabase.ai) and one made up for the game.
Spot the real threat and the building is protected. Miss it and the city pays.

10 buildings, 17 languages, one static HTML page.

## Layout

| Path | What it is |
|---|---|
| `ai_incident_game_seed_v3.yaml` | Source content in English: the incidents, the made-up counterparts, the "what if" scenarios |
| `translations/<lang>.yaml` | Interface strings and incident texts per language (`en.yaml` holds only the English interface and extras) |
| `site/src/game.html` | The page template: layout, styles, the isometric city, game logic |
| `site/build.py` | Merges the seed and translations into the page |
| `docs/index.html` | The built site, served by GitHub Pages |

## Build

```
pip install pyyaml
python3 site/build.py
```

This rewrites `docs/index.html`. Commit and push it to publish.

## Publish on GitHub Pages

In the repository: Settings → Pages → Source: "Deploy from a branch" → Branch `main`, folder `/docs`.

## Editing content

- Which incident sits in which building: `BUILDINGS` in `site/build.py`.
- Language order in the menu: `MAIN_LANGS` / `MORE_LANGS` in `site/build.py`.
- Bold phrases in the two reports: the `highlight` lists in each translation file. The build warns if a phrase is not found in its text.
- The made-up reports are fiction. Before publishing, check each against the AI Incident Database so none duplicates a real case.
