# UI Feature Parity Guide

The old `app.py` had a tabbed interface with features that are missing from the current step-based `ui.html`. This document outlines what needs to be added.

## Current State

**`ui.html` (step-based)**:
- Step 1: Discover URL
- Step 2: Edit Configuration (JSON editor)
- Step 3: Fetch Links (manual site ID input)
- Step 4: Scrape Content (manual site ID + path input)
- Step 5: Export URLs

**Old `app.py` HTML (tabbed)**:
- Sites tab: Browse & test existing sites
- Discover tab: Analyze new URLs
- Bulk Jobs tab: Submit and monitor bulk scrapes

---

## Features to Add

### 1. Site List on Page Load

**What it did**: Fetched all configured sites from `/api/sites` and displayed them in a grid on page load.

**Implementation**:
```javascript
async function loadSites() {
  const res = await fetch(`${API}/sites`);
  const data = await res.json();
  // data.sites is an array of {id, name, baseUrl, ...}
}
```

**UI Elements needed**:
```html
<div id="siteList" class="site-list">
  <!-- Populated dynamically -->
  <div class="site-item" onclick="selectSite('modal')">
    <div class="name">modal</div>
  </div>
</div>
```

**CSS**:
```css
.site-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
.site-item {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
}
.site-item:hover { border-color: #58a6ff; }
```

---

### 2. Pre-populated Site Dropdown

**What it did**: A `<select>` dropdown auto-filled with all site IDs when the page loads.

**Implementation**:
```javascript
// After loading sites
const select = document.getElementById('testSiteId');
select.innerHTML = data.sites.map(s =>
  `<option value="${s.id}">${s.id}</option>`
).join('');
```

**Where to add in ui.html**:
- Step 3 (Fetch Links): Replace text input with dropdown
- Step 4 (Scrape Content): Replace text input with dropdown
- Step 5 (Export): Already has this for cache loading

---

### 3. Click Site to Auto-fill

**What it did**: Clicking a site in the grid auto-selected it in the dropdown.

**Implementation**:
```javascript
function selectSite(siteId) {
  document.getElementById('testSiteId').value = siteId;
  // Also fill in other site ID inputs
  document.getElementById('linksSiteId').value = siteId;
  document.getElementById('contentSiteId').value = siteId;
}
```

---

### 4. Bulk Jobs Tab

**What it did**: Submit a list of URLs for parallel scraping with job tracking.

**Endpoints used**:
- `POST /api/jobs/bulk` - Submit job, returns `{job_id, status, batches}`
- `GET /api/jobs` - List recent jobs
- `GET /api/jobs/{job_id}` - Get job status with progress

**UI Elements**:
```html
<!-- Submit Job -->
<textarea id="bulkUrls" placeholder="Paste URLs (one per line)"></textarea>
<button onclick="submitBulk()">Submit Job</button>

<!-- Recent Jobs List -->
<div id="jobsList"></div>

<!-- Job Progress -->
<div id="jobDetail">
  <div class="progress-bar">
    <div class="progress-fill" id="jobProgress"></div>
  </div>
  <div class="job-stats">
    <div>Completed: <span id="jobCompleted">0</span></div>
    <div>Success: <span id="jobSuccess">0</span></div>
    <div>Failed: <span id="jobFailed">0</span></div>
    <div>Skipped: <span id="jobSkipped">0</span></div>
  </div>
</div>
```

---

### 5. Live Job Progress Polling

**What it did**: Polled job status every 2 seconds until completion.

**Implementation**:
```javascript
let pollInterval = null;

async function watchJob(jobId) {
  if (pollInterval) clearInterval(pollInterval);

  const updateJob = async () => {
    const res = await fetch(`${API}/jobs/${jobId}`);
    const data = await res.json();

    document.getElementById('jobProgress').style.width = `${data.progress_pct}%`;
    document.getElementById('jobCompleted').textContent = data.progress?.completed || 0;
    document.getElementById('jobSuccess').textContent = data.progress?.success || 0;
    document.getElementById('jobFailed').textContent = data.progress?.failed || 0;
    document.getElementById('jobSkipped').textContent = data.progress?.skipped || 0;

    if (data.status === 'completed') {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  };

  updateJob();
  pollInterval = setInterval(updateJob, 2000);
}
```

---

### 6. Loading States

**What it did**: Showed skeleton loaders and spinners during async operations.

**CSS**:
```css
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
}
.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #30363d;
  border-top-color: #58a6ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.skeleton {
  background: linear-gradient(90deg, #21262d 25%, #30363d 50%, #21262d 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

---

### 7. Tabbed Interface (Optional)

**What it did**: Organized features into tabs instead of sequential steps.

**Tabs**:
- **Sites**: Browse existing sites, test links/content
- **Discover**: Analyze new URLs, get config suggestions
- **Bulk Jobs**: Submit and monitor bulk scrapes
- **Export**: Download docs as ZIP

**Implementation**:
```javascript
function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`[onclick="showTab('${name}')"]`).classList.add('active');
  document.getElementById(`${name}-panel`).classList.add('active');

  // Auto-load data when switching tabs
  if (name === 'sites') loadSites();
  if (name === 'bulk') loadJobs();
}
```

---

## API Endpoints Reference

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/sites` | GET | List all configured sites | `{sites: [{id, name, ...}]}` |
| `/api/sites/{id}/links` | GET | Get links for a site | `{links: [...], count: n}` |
| `/api/sites/{id}/content` | GET | Get page content | `{content: "...", from_cache: bool}` |
| `/api/discover` | GET | Analyze a URL | `{framework, base_url_suggestion, ...}` |
| `/api/jobs/bulk` | POST | Submit bulk job | `{job_id, status, batches}` |
| `/api/jobs` | GET | List recent jobs | `{jobs: [...]}` |
| `/api/jobs/{id}` | GET | Get job status | `{progress_pct, progress: {...}}` |
| `/api/cache/keys` | GET | List cached URLs | `{keys: [{url}], count: n}` |
| `/api/export` | POST | Export as ZIP | `{zip_base64, stats}` |

---

## Priority Order

1. **High**: Pre-populated site dropdown (improves UX significantly)
2. **High**: Site list on page load (shows what's available)
3. **Medium**: Click-to-select site (convenience feature)
4. **Medium**: Bulk jobs submission (useful for large scrapes)
5. **Low**: Job progress tracking (nice to have)
6. **Low**: Tabbed interface (requires significant restructure)

---

## Quick Win: Add Site Dropdown

Replace the text input in Steps 3-4 with a select that loads on page init:

```html
<!-- Replace this -->
<input type="text" id="linksSiteId" placeholder="my-site">

<!-- With this -->
<select id="linksSiteId"></select>
```

```javascript
// Add to page init
window.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch(`${API}/sites`);
    const data = await res.json();
    const sites = data.sites || [];

    const options = sites.map(s =>
      `<option value="${s.id}">${s.id}</option>`
    ).join('');

    document.getElementById('linksSiteId').innerHTML = options;
    document.getElementById('contentSiteId').innerHTML = options;
  } catch (err) {
    console.error('Failed to load sites:', err);
  }
});
```
