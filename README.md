# Create DeepSeek from scratch

[Read the public course](https://vukrosic.github.io/deepseek-from-scratch/) · [Engram vs LoRA research](https://vukrosic.github.io/deepseek-from-scratch/#engram-research)

Independent, evolving educational course by Vuk Rosić. It does not claim to reproduce a full production DeepSeek model.

The course is authored in small lesson HTML files and compiled into one portable page. No frontend framework or npm install is required.

## Edit and preview

1. Edit the relevant file in `lessons/`. `index.template.html` owns navigation and page layout. Engram's parent fragment includes the individual parts in order.
2. Run `python3 build_course.py`, or run `python3 serve.py` and reload the page. The course server rebuilds before serving the main page.
3. Open http://127.0.0.1:8766/ . Use the page's Edit text button for saved prose changes.

Do not directly edit generated `index.html`. It is retained for static hosting. Never use plain `http.server` for the authoring session: it cannot save text edits or rebuild lessons.

## File map

- `index.template.html`: site shell, navigation, ordered section includes.
- `lessons/*.html`: chapter and individual lesson source. Current Engram parts, paper introduction, official README guide and first code exercise are separate files.
- `build_course.py`: dependency-free include expansion, unique-ID and saved-edit checks; atomic output.
- `serve.py`: localhost server with rebuild and autosave.
- `content/text-edits.json`: user's saved text overrides; these take precedence over HTML text.
- `content/text-edit-history.jsonl`: append-only edit history.
- `content/engram-*.json`: lesson/video metadata.
- `assets/`: portable media, official sources, licenses and provenance.
- `exercises/packed_lookup.py`: tiny dependency-free code exercise.
- `offset-exercise.js`: browser equivalent; it does not execute Python.
- `engram-lab-core.js`, `engram-lab-ui.js`: existing seeded, untrained mechanism lab.
- `style.css`, `app.js`, `editor.js`: shared appearance, interactions and editor.

Keep stable data-edit-id values. Read text-edits.json before revising existing content. New fields need new IDs. Video narration is a separate saved snapshot; editing the article does not change a finished video. Only the opening currently has user approval.

## Checks

`python3 build_course.py --check`

`python3 -m unittest discover -s tests -p 'test_*.py'`

`node tests/engram-lab.test.cjs`

`python3 exercises/packed_lookup.py`

The one-time migration snapshot at content/pre-modular-index.html records the initial lossless split. It is historical evidence, not a source file; future edits need not match it.

## Growing into a longer course

Add lessons as independent fragments. Media already loads on demand. The build approach lets us later generate one page per chapter while retaining the same lesson sources. For now, all chapter links and existing saved edits remain compatible. A framework is not needed for the present interactions.

For static hosting, build first and publish the generated site when explicitly authorized. GitHub Pages serves the main branch. Public readers see learner view and saved article text; author controls and disk autosave remain local. Rebuild and commit the generated page when publishing an update.

## Attribution

Original Engram figures/code/README and its Apache-2.0 license are preserved in assets/engram-official, with provenance. The paper's first page is rendered from the repository's original PDF. Research results belong to their authors; our fixed-array exercises do not reproduce their trained benchmarks. Other media retains its original provenance; no blanket license is asserted over all course assets. Editable video sources remain in the parent course directory.

## Recorded video editing

Editable video production projects stay outside this public repository. The course includes rendered teaching clips and their attribution.
