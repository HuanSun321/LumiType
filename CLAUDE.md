# TypeHan 打字汉

PyQt6 中文打字练习应用。手绘可爱风格 UI。

## Structure

- `main.py` — entry point
- `src/app.py` — singleton App (config + db)
- `src/config.py` — QSettings wrapper
- `src/constants.py` — colors, timing, fonts
- `src/core/` — game_engine, game_state, scoring, statistics
- `src/db/database.py` — SQLite storage
- `src/materials/` — material_manager, material_store, scrapers/
- `src/modes/` — follow_typing, falling_text, timed_challenge
- `src/ui/theme.py` — ThemeManager + stylesheet
- `src/ui/main_window.py` — QStackedWidget router
- `src/ui/screens/` — menu, game, results, settings, stats, material
- `src/ui/widgets/` — input_bar, text_display, combo_display, falling_item, progress_ring
- `data/builtin/` — sample_poems.json, common_idioms.json

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Design Style

手绘可爱风格 (hand-drawn cute):
- Pastel color palette (soft pink, lavender, mint, cream)
- Rounded corners, bubbly shapes
- Playful emoji accents
- Soft shadows, warm tones
