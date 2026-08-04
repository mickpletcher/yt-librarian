# Troubleshooting

## The browser says the profile is in use

Close every browser created by `ykm browser-login` or sync. The dedicated profile cannot be opened by two Chromium processes at once.

## Login or security intervention required

Run `uv run ykm browser-login`, handle the prompt manually, close the browser, and rerun the command. Never copy cookies into configuration.

## No videos are found

Confirm the profile can open `https://www.youtube.com/playlist?list=LL`. YouTube may have changed its DOM. Run the mocked test suite first, then inspect selectors in `browser/selectors.py` with a dry run.

## SQLite is locked

Close Streamlit and other CLI processes using the database. The application configures a busy timeout, but only one writer should run at a time.

## A playlist cannot be found

Ensure the local category playlist name exactly matches a visible YouTube playlist. If a playlist identifier is known, store it on the category. Planning will skip categories without either mapping.

## Reset local state

Back up and remove only `data/youtube_knowledge_manager.sqlite3`, then rerun `alembic upgrade head`. Never delete the entire repository or browser profile as a troubleshooting shortcut.
