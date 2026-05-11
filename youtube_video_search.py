import requests
import json
import datetime
import math
import sys
from pathlib import Path

# ===== CONFIGURATION =====
API_KEY = "AIzaSyBTywdvYzEJlu1Q0782hI0iM22zBZIWCcc"

def get_config():
    """Get search query and output filename from args or input."""
    query = None
    output_html = None

    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_html = sys.argv[2]

    if not query:
        query = input("Enter search keyword or @handle: ").strip()
    
    # If it starts with @, treat as handle search
    is_handle = query.startswith("@")
    clean_query = query.replace("@", "")

    if not output_html:
        safe_name = "".join(x for x in clean_query if x.isalnum() or x in "._- ").strip().replace(" ", "_")
        output_html = f"youtube_{safe_name}_dashboard.html"
    
    return query, clean_query, is_handle, output_html

QUERY, SEARCH_TERM, IS_HANDLE, OUTPUT_HTML = get_config()
# ============================

def iso8601_duration_to_minutes(duration_str):
    """Convert ISO 8601 duration to a string like '12:34' or '1:02:01'."""
    import re
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    if not match:
        return duration_str
    h, m, s = match.groups()
    h = int(h) if h else 0
    m = int(m) if m else 0
    s = int(s) if s else 0
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    else:
        return f"{m}:{s:02d}"

def get_channel_id(api_key, handle):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "id", "forHandle": handle, "key": api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("items"):
        raise ValueError(f"No channel found for handle @{handle}")
    return data["items"][0]["id"]

def get_uploads_playlist_id(api_key, channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "contentDetails", "id": channel_id, "key": api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def fetch_videos_by_search(api_key, query, max_results=100):
    videos = []
    next_page_token = None
    url = "https://www.googleapis.com/youtube/v3/search"
    
    while len(videos) < max_results:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(50, max_results - len(videos)),
            "key": api_key,
        }
        if next_page_token:
            params["pageToken"] = next_page_token
            
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get("items"):
            break

        video_ids = [item["id"]["videoId"] for item in data["items"]]
        
        # Enrich with stats
        stats_params = {
            "part": "statistics,contentDetails,snippet",
            "id": ",".join(video_ids),
            "key": api_key,
        }
        stats_resp = requests.get("https://www.googleapis.com/youtube/v3/videos", params=stats_params)
        stats_resp.raise_for_status()
        stats_data = stats_resp.json()
        
        for vid_item in stats_data["items"]:
            snippet = vid_item["snippet"]
            stats = vid_item.get("statistics", {})
            content = vid_item.get("contentDetails", {})
            
            videos.append({
                "title": snippet.get("title", ""),
                "publishedAt": snippet.get("publishedAt", ""),
                "views": int(stats.get("viewCount", 0)),
                "duration": iso8601_duration_to_minutes(content.get("duration", "")),
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "url": f"https://www.youtube.com/watch?v={vid_item['id']}"
            })
            
        next_page_token = data.get("nextPageToken")
        if not next_page_token or len(videos) >= max_results:
            break
            
    return videos

def fetch_all_from_playlist(api_key, playlist_id):
    videos = []
    next_page_token = None
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    while True:
        params = {
            "part": "snippet,contentDetails",
            "maxResults": 50,
            "playlistId": playlist_id,
            "key": api_key,
        }
        if next_page_token:
            params["pageToken"] = next_page_token
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        video_ids = [item["contentDetails"]["videoId"] for item in data["items"]]
        stats_params = {"part": "statistics,contentDetails,snippet", "id": ",".join(video_ids), "key": api_key}
        stats_resp = requests.get("https://www.googleapis.com/youtube/v3/videos", params=stats_params)
        stats_resp.raise_for_status()
        stats_data = stats_resp.json()
        stats_lookup = {vid["id"]: vid for vid in stats_data["items"]}
        for item in data["items"]:
            vid = item["contentDetails"]["videoId"]
            snippet = item["snippet"]
            stats = stats_lookup.get(vid, {})
            content = stats.get("contentDetails", {})
            stats_detail = stats.get("statistics", {})
            videos.append({
                "title": snippet.get("title", ""),
                "publishedAt": snippet.get("publishedAt", ""),
                "views": int(stats_detail.get("viewCount", 0)),
                "duration": iso8601_duration_to_minutes(content.get("duration", "")),
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "url": f"https://www.youtube.com/watch?v={vid}"
            })
        next_page_token = data.get("nextPageToken")
        if not next_page_token: break
    return videos

if IS_HANDLE:
    print(f"Searching by Channel Handle: @{SEARCH_TERM}")
    channel_id = get_channel_id(API_KEY, SEARCH_TERM)
    playlist_id = get_uploads_playlist_id(API_KEY, channel_id)
    videos = fetch_all_from_playlist(API_KEY, playlist_id)
else:
    print(f"Searching by Keyword: '{QUERY}'")
    videos = fetch_videos_by_search(API_KEY, QUERY)

print(f"Fetched {len(videos)} videos.")

# Create self-contained HTML
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{QUERY} - Video Dashboard</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f9f9f9; color: #333; }}
  h1 {{ margin-bottom: 0.2em; }}
  .filters {{ display: flex; flex-wrap: wrap; gap: 15px; margin: 15px 0; align-items: center; }}
  .filters label {{ font-weight: 600; }}
  input, button {{ padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 0.9em; }}
  button {{ background: #007bff; color: white; border: none; cursor: pointer; }}
  button:hover {{ background: #0056b3; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  th, td {{ padding: 10px 12px; text-align: left; }}
  th {{ background: #007bff; color: white; cursor: pointer; user-select: none; position: sticky; top: 0; }}
  th:hover {{ background: #0056b3; }}
  th .sort-icon {{ margin-left: 4px; font-size: 0.8em; }}
  tr:nth-child(even) {{ background: #f2f2f2; }}
  tr:hover {{ background: #e6f0ff; }}
  .thumbnail {{ width: 120px; height: 68px; object-fit: cover; border-radius: 4px; }}
  .views {{ font-weight: 600; }}
  .search-box {{ flex-grow: 1; }}
  #reset-filters {{ background: #6c757d; }}
  #reset-filters:hover {{ background: #545b62; }}
</style>
</head>
<body>
<h1>YouTube Video Dashboard: {QUERY}</h1>
<p>Total videos: {len(videos)}</p>

<div class="filters">
  <div class="search-box">
    <label for="search">🔍 Search title:</label>
    <input type="text" id="search" placeholder="Type to filter..." style="width:250px;">
  </div>
  <div>
    <label for="date-from">From:</label>
    <input type="date" id="date-from">
  </div>
  <div>
    <label for="date-to">To:</label>
    <input type="date" id="date-to">
  </div>
  <div>
    <label for="min-views">Min views:</label>
    <input type="number" id="min-views" placeholder="0" style="width:100px;" min="0">
  </div>
  <button id="reset-filters">Reset Filters</button>
</div>

<table id="video-table">
  <thead>
    <tr>
      <th data-sort="thumbnail">Thumbnail</th>
      <th data-sort="title">Title</th>
      <th data-sort="publishedAt">Upload Date</th>
      <th data-sort="views">Views</th>
      <th data-sort="duration">Duration</th>
    </tr>
  </thead>
  <tbody>
    <!-- Data will be rendered here by JavaScript -->
  </tbody>
</table>

<script>
// Video data directly embedded from the API fetch
const VIDEOS = {json.dumps(videos, indent=2)};

let currentSort = {{ field: 'publishedAt', order: 'desc' }};  // default: newest first
let filteredData = [...VIDEOS];

function formatDate(isoString) {{
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleDateString('en-US', {{ year: 'numeric', month: 'short', day: 'numeric' }});
}}

function formatViews(views) {{
  return views.toLocaleString();
}}

function renderTable(data) {{
  const tbody = document.querySelector('#video-table tbody');
  tbody.innerHTML = '';
  if (data.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px;">No videos match the filters.</td></tr>';
    return;
  }}
  data.forEach(video => {{
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><a href="${{video.url}}" target="_blank"><img src="${{video.thumbnail}}" alt="thumbnail" class="thumbnail" loading="lazy"></a></td>
      <td><a href="${{video.url}}" target="_blank" style="text-decoration:none; color:#007bff;">${{video.title}}</a></td>
      <td>${{formatDate(video.publishedAt)}}</td>
      <td class="views">${{formatViews(video.views)}}</td>
      <td>${{video.duration}}</td>
    `;
    tbody.appendChild(row);
  }});
}}

function applyFilters() {{
  const searchText = document.getElementById('search').value.toLowerCase();
  const dateFrom = document.getElementById('date-from').value;
  const dateTo = document.getElementById('date-to').value;
  const minViews = parseInt(document.getElementById('min-views').value) || 0;
  
  filteredData = VIDEOS.filter(v => {{
    // Search by title
    if (searchText && !v.title.toLowerCase().includes(searchText)) return false;
    
    // Date range
    if (dateFrom && v.publishedAt < dateFrom) return false;
    if (dateTo) {{
      // Include whole day of dateTo by adding one day and comparing <
      const nextDay = new Date(dateTo);
      nextDay.setDate(nextDay.getDate() + 1);
      if (v.publishedAt >= nextDay.toISOString().split('T')[0]) return false;
    }}
    
    // Minimum views
    if (v.views < minViews) return false;
    
    return true;
  }});
  
  // Re-apply current sort on filtered data
  sortData(currentSort.field, currentSort.order, true);
}}

function sortData(field, order, skipToggle = false) {{
  if (!skipToggle) {{
    if (currentSort.field === field) {{
      currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
    }} else {{
      currentSort.field = field;
      currentSort.order = 'asc';  // default asc when changing field
    }}
  }}
  const direction = currentSort.order === 'asc' ? 1 : -1;
  
  filteredData.sort((a, b) => {{
    let valA, valB;
    if (field === 'publishedAt') {{
      valA = a.publishedAt || '';
      valB = b.publishedAt || '';
    }} else if (field === 'views') {{
      valA = a.views;
      valB = b.views;
    }} else if (field === 'duration') {{
      // Convert "M:SS" or "H:MM:SS" to total seconds for comparison
      const toSeconds = (str) => {{
        const parts = str.split(':').map(Number);
        if (parts.length === 3) return parts[0]*3600 + parts[1]*60 + parts[2];
        if (parts.length === 2) return parts[0]*60 + parts[1];
        return 0;
      }};
      valA = toSeconds(a.duration);
      valB = toSeconds(b.duration);
    }} else if (field === 'title') {{
      valA = a.title.toLowerCase();
      valB = b.title.toLowerCase();
    }} else if (field === 'thumbnail') {{
      // Sort by title if thumbnail column clicked (just because)
      valA = a.title.toLowerCase();
      valB = b.title.toLowerCase();
    }}
    
    if (valA < valB) return -1 * direction;
    if (valA > valB) return 1 * direction;
    return 0;
  }});
  
  renderTable(filteredData);
  updateSortIcons();
}}

function updateSortIcons() {{
  document.querySelectorAll('th').forEach(th => {{
    const field = th.dataset.sort;
    const icon = th.querySelector('.sort-icon');
    if (icon) {{
      if (field === currentSort.field) {{
        icon.textContent = currentSort.order === 'asc' ? ' ▲' : ' ▼';
      }} else {{
        icon.textContent = '';
      }}
    }}
  }});
}}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {{
  // Initial render
  applyFilters();
  
  // Add sort icons to header cells
  document.querySelectorAll('th').forEach(th => {{
    const icon = document.createElement('span');
    icon.className = 'sort-icon';
    th.appendChild(icon);
  }});
  
  // Sort click handlers
  document.querySelectorAll('th').forEach(th => {{
    th.addEventListener('click', () => {{
      const field = th.dataset.sort;
      if (field) {{
        sortData(field, null);
      }}
    }});
  }});
  
  // Filter events
  document.getElementById('search').addEventListener('input', applyFilters);
  document.getElementById('date-from').addEventListener('change', applyFilters);
  document.getElementById('date-to').addEventListener('change', applyFilters);
  document.getElementById('min-views').addEventListener('input', applyFilters);
  
  // Reset
  document.getElementById('reset-filters').addEventListener('click', () => {{
    document.getElementById('search').value = '';
    document.getElementById('date-from').value = '';
    document.getElementById('date-to').value = '';
    document.getElementById('min-views').value = '';
    applyFilters();
  }});
  
  updateSortIcons();
}});
</script>
</body>
</html>"""

# Write file
OUTPUT_PATH.write_text(html_content, encoding='utf-8')
print(f"Dashboard saved to {OUTPUT_PATH}")
print("Open it in your browser. All data is embedded – no server needed.")
t, encoding='utf-8')
print(f"Dashboard saved to {OUTPUT_HTML}")
print("Open it in your browser. All data is embedded – no server needed.")
