# UI Redesign Plan

## Vision
A clean, modern single-page app that makes it easy to browse existing sites, discover new ones, and export documentation.

## Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Docpull                                         [Sites: 12]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Your Sites                                [Refresh]     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │  modal   │ │ vercel   │ │ supabase │ │ + Add    │    │   │
│  │  │  42 docs │ │ 128 docs │ │ 89 docs  │ │  New     │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Quick Actions                                           │   │
│  │                                                          │   │
│  │  Site: [modal ▼]  Path: [/guide/___________]            │   │
│  │                                                          │   │
│  │  [View Links]  [Preview Content]  [Export Site]         │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Add New Site                                            │   │
│  │                                                          │   │
│  │  URL: [https://docs.example.com/________] [Discover]    │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ {                                                │    │   │
│  │  │   "name": "example",                             │    │   │
│  │  │   "baseUrl": "https://docs.example.com"          │    │   │
│  │  │ }                                                │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                            [Save Config] │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Export                                                  │   │
│  │                                                          │   │
│  │  [Load from modal ▼]  or paste URLs below:              │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ https://modal.com/docs/guide                     │    │   │
│  │  │ https://modal.com/docs/reference                 │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │  [ ] Scrape missing (slower)         [Export as ZIP]    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Changes

### 1. Sites Grid at Top
- Load sites on page init via `GET /api/sites`
- Show site cards with name and doc count (if available)
- Click card → selects site in all dropdowns
- "+ Add New" card opens the discover section

### 2. Unified Site Selector
- Single dropdown shared across sections
- Auto-populated on page load
- Selecting updates all related inputs

### 3. Collapsible Sections
- Each card can collapse/expand
- Remember state in localStorage
- Cleaner when only using one feature

### 4. Better Visual Hierarchy
- Sites grid = primary (what you have)
- Quick actions = secondary (test existing)
- Add new = tertiary (occasional use)
- Export = utility (end of workflow)

### 5. Output Panel
- Slide-out or modal for results
- Syntax highlighting for markdown preview
- Copy button for content

## Implementation Steps

### Phase 1: Site Loading (Core)
1. Add `loadSites()` function that calls `GET /api/sites`
2. Create site card grid HTML structure
3. Add CSS for grid layout
4. Call `loadSites()` on DOMContentLoaded
5. Populate all `<select>` elements with sites

### Phase 2: Quick Actions Section
1. Replace Steps 3-4 with unified "Quick Actions" card
2. Single site dropdown + path input
3. Three buttons: Links, Content, Export Site
4. Output area below buttons

### Phase 3: Discover Improvements
1. Keep discover URL input
2. Auto-parse config from response
3. Pre-fill site ID from URL hostname
4. "Save & Test" button combo

### Phase 4: Export Enhancements
1. "Load from [site]" button to fetch cached URLs
2. URL count indicator
3. Progress feedback during export

### Phase 5: Polish
1. Loading skeletons for site grid
2. Toast notifications for success/error
3. Keyboard shortcuts (Cmd+Enter to submit)
4. Dark/light theme toggle (optional)

## Files to Modify

- `ui/ui.html` - Main changes
- `ui/server.py` - May need endpoint tweaks
- `ui/app.py` - Ensure endpoint parity

## CSS Variables (Design System)

```css
:root {
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-tertiary: #21262d;
  --border: #30363d;
  --text-primary: #c9d1d9;
  --text-secondary: #8b949e;
  --accent: #58a6ff;
  --success: #238636;
  --error: #f85149;
  --radius: 8px;
  --spacing: 16px;
}
```

## Success Criteria

- [ ] Sites load automatically on page open
- [ ] Can select a site and immediately test links/content
- [ ] Discover → Save → Test flow is seamless
- [ ] Export works with one click for a whole site
- [ ] Works on both local server and deployed Modal
- [ ] Mobile responsive (nice to have)
