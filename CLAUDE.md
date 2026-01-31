# CLAUDE.md

Modal-based documentation scraper. See README.md for usage.

## Maintaining This Project

### Adding New Sites

1. Use `discover` to generate initial config from any doc URL
2. Add config to `scraper/config/sites.json`
3. Test with `links` command to verify URL patterns work
4. Test with `content` command on a sample page
5. Adjust selectors in config if content extraction is incorrect

### Development Workflow

- **Local testing**: `modal serve content-scraper-api.py` for API hot-reload
- **UI development**: Run `python ui/setup.py` once, then `modal serve ui/app.py`
- **Config changes**: Edit `scraper/config/sites.json`, test immediately (no redeploy needed)
- **API changes**: Hot-reload in serve mode automatically applies changes

### Key Configuration Points

- `scraper/config/sites.json` - All site definitions
- Site configs use either `fetch` (fast, simple) or `browser` (JS-heavy sites) mode
- Content selectors must be CSS or XPath strings
- Link patterns use regex to filter relevant URLs

### Testing Changes

Before committing changes:
- Verify existing sites still work with `sites` command
- Test new configs with both `links` and `content` commands
- Check that output markdown is properly formatted
- Use `--force` flag to bypass cache when testing fixes
