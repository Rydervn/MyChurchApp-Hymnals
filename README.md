# MyChurchApp Hymnals

Hymnals that the MyChurchApp mobile app downloads for offline use, the same way it downloads Bible versions.

The app reads `index.json` from this repository's raw URL (set in `ApiUrl.HYMNALS_BASEURL` in the Flutter app):

```
https://raw.githubusercontent.com/Rydervn/MyChurchApp-Hymnals/main/index.json
```

## Layout

| Path | What it is |
|---|---|
| `index.json` | The catalog shown on the app's "Download Hymnals" screen |
| `hymnals/<code>.json` | One hymnal: metadata plus every hymn with its verses |
| `tools/build_hymnals.py` | Regenerates both from the raw sources |

A hymnal file looks like this:

```json
{
  "id": 1, "code": "sda-hymnal-en", "name": "SDA Hymnal", "language": "English",
  "description": "...", "version": 1, "count": 694,
  "hymns": [
    {"id": 100001, "number": "1", "title": "Praise to the Lord",
     "verses": [{"label": "1", "text": "Praise to the Lord, the Almighty,\n..."},
                {"label": "Refrain", "text": "..."}]}
  ]
}
```

A verse `label` is a verse number, `Chorus`/`Refrain`, or a voice part (`Soprano`, `Alto`...). An optional `subtitle` holds the English title of a translated hymn.

## Updating hymnals

1. Edit the raw sources (default `F:/church/Hymnals`).
2. In `tools/build_hymnals.py`, bump the hymnal's `version`. The app offers an **Update** to anyone with an older copy.
3. Run `python tools/build_hymnals.py [SOURCE_DIR]` and commit the changed `index.json` and `hymnals/` files.

To add a hymnal, append an entry to `HYMNALS` with the next free `id`.

Never renumber existing hymnals or hymns. Hymn ids are `hymnal id * 100000 + position`, and the app uses them to remember bookmarks. Add new hymns at the end of a hymnal's numbering where possible.
