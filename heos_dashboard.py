from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import requests
import xml.etree.ElementTree as ET
import json
import os
import pickle

app = Flask(__name__)

# Define PRESET_STATIONS as global
global PRESET_STATIONS

DEVICE_IP = "10.29.60.78"
PORT = 60006
CONTROL_URL = f"http://{DEVICE_IP}:{PORT}/upnp/control/renderer_dvc/AVTransport"
HEADERS = {
    "Content-Type": 'text/xml; charset="utf-8"',
}

# File to store custom stations
STATIONS_FILE = "custom_stations.pkl"

# Default preset stations
DEFAULT_STATIONS = [
    {"name": "NPR", "uri": "https://npr-ice.streamguys1.com/live.mp3"},
    {"name": "Classic FM", "uri": "http://media-ice.musicradio.com/ClassicFMMP3.m3u"}
]

# Load custom stations or use defaults if file doesn't exist
def load_stations():
    try:
        if os.path.exists(STATIONS_FILE):
            with open(STATIONS_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        print(f"Error loading stations: {e}")
    return DEFAULT_STATIONS

# Save stations to file
def save_stations(stations):
    try:
        with open(STATIONS_FILE, 'wb') as f:
            pickle.dump(stations, f)
        return True
    except Exception as e:
        print(f"Error saving stations: {e}")
        return False

# Initialize stations list
PRESET_STATIONS = load_stations()

def build_soap_envelope(action, service, body_xml):
    return f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\"
            s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">
  <s:Body>
    <u:{action} xmlns:u=\"{service}\">
      {body_xml}
    </u:{action}>
  </s:Body>
</s:Envelope>"""

def send_upnp_action(action, body_xml, service="urn:schemas-upnp-org:service:AVTransport:1", control_url=CONTROL_URL):
    headers = HEADERS.copy()
    headers["SOAPACTION"] = f'"{service}#{action}"'
    envelope = build_soap_envelope(action, service, body_xml)
    response = requests.post(control_url, data=envelope, headers=headers)
    return response.text

def set_uri(uri):
    xml_body = f"""
    <InstanceID>0</InstanceID>
    <CurrentURI>{uri}</CurrentURI>
    <CurrentURIMetaData></CurrentURIMetaData>
    """
    return send_upnp_action("SetAVTransportURI", xml_body)

def play():
    return send_upnp_action("Play", "<InstanceID>0</InstanceID><Speed>1</Speed>")

def stop():
    return send_upnp_action("Stop", "<InstanceID>0</InstanceID>")

def pause():
    return send_upnp_action("Pause", "<InstanceID>0</InstanceID>")

def power_off():
    power_service = "urn:schemas-denon-com:service:ACT:1"
    power_control_url = f"http://{DEVICE_IP}:{PORT}/ACT/control"
    return send_upnp_action("PutPowerState", "<Power>Off</Power>", service=power_service, control_url=power_control_url)

def get_status():
    raw_xml = send_upnp_action("GetTransportInfo", "<InstanceID>0</InstanceID>")
    try:
        root = ET.fromstring(raw_xml)

        def find_text(tag_name):
            for elem in root.iter():
                if elem.tag.endswith(tag_name):
                    return elem.text
            return "N/A"

        return {
            "Transport State": find_text("CurrentTransportState"),
            "Transport Status": find_text("CurrentTransportStatus"),
            "Playback Speed": find_text("CurrentSpeed")
        }

    except Exception as e:
        return {
            "Error": f"Failed to parse SOAP response: {e}",
            "Raw Response": raw_xml
        }

def get_volume():
    CONTROL_URL_VOL = f"http://{DEVICE_IP}:{PORT}/upnp/control/renderer_dvc/RenderingControl"
    headers = HEADERS.copy()
    headers["SOAPACTION"] = "\"urn:schemas-upnp-org:service:RenderingControl:1#GetVolume\""
    envelope = build_soap_envelope("GetVolume",
        "urn:schemas-upnp-org:service:RenderingControl:1",
        "<InstanceID>0</InstanceID><Channel>Master</Channel>"
    )
    response = requests.post(CONTROL_URL_VOL, data=envelope, headers=headers)
    try:
        root = ET.fromstring(response.text)
        for elem in root.iter():
            if elem.tag.endswith("CurrentVolume"):
                return elem.text
    except Exception:
        pass
    return "0"

def set_volume(level):
    CONTROL_URL_VOL = f"http://{DEVICE_IP}:{PORT}/upnp/control/renderer_dvc/RenderingControl"
    headers = HEADERS.copy()
    headers["SOAPACTION"] = "\"urn:schemas-upnp-org:service:RenderingControl:1#SetVolume\""
    envelope = build_soap_envelope("SetVolume",
        "urn:schemas-upnp-org:service:RenderingControl:1",
        f"<InstanceID>0</InstanceID><Channel>Master</Channel><DesiredVolume>{level}</DesiredVolume>"
    )
    requests.post(CONTROL_URL_VOL, data=envelope, headers=headers)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Marantz HEOS Control</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-color: #f8f9fa;
            --text-color: #212529;
            --card-bg: #ffffff;
            --control-bg: #f8f9fa;
            --border-color: #dee2e6;
            --slider-bg: #ccc;
            --slider-thumb: #0d6efd;
        }
        
        .dark-mode {
            --bg-color: #121212;
            --text-color: #e0e0e0;
            --card-bg: #1e1e1e;
            --control-bg: #2a2a2a;
            --border-color: #444444;
            --slider-bg: #555;
            --slider-thumb: #3a8eff;
        }
        
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color 0.3s, color 0.3s;
        }
        
        .btn {
            margin: 0 5px;
        }
        
        .station-btn {
            margin: 5px;
        }
        
        .volume-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 10px;
            width: 100%;
        }
        
        .volume-display {
            margin-top: 10px;
            font-weight: bold;
            font-size: 1.2rem;
        }
        
        .form-range {
            height: 10px;
            background-color: var(--slider-bg);
            border-radius: 5px;
        }
        
        .form-range::-webkit-slider-thumb {
            background: var(--slider-thumb);
        }
        
        .form-range::-moz-range-thumb {
            background: var(--slider-thumb);
        }
        
        .control-section {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 8px;
            background-color: var(--control-bg);
            border: 1px solid var(--border-color);
            height: 100%;
        }
        
        .station-controls {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .station-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .status-section {
            margin-top: 30px;
        }
        
        .save-station-form {
            margin-top: 15px;
        }
        
        .card {
            background-color: var(--card-bg);
            border-color: var(--border-color);
        }
        
        .list-group-item {
            background-color: var(--card-bg);
            color: var(--text-color);
            border-color: var(--border-color);
        }
        
        .theme-toggle {
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 1000;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        .station-action-btn {
            padding: 2px 6px;
            font-size: 0.8rem;
        }
    </style>
</head>
<body class="bg-light">
    <div class="container py-5">
    <h1 class="mb-4 text-center">🎶 Marantz HEOS Control Dashboard</h1>
    
    <div class="row">
        <!-- Stations Section -->
        <div class="col-md-8">
            <div class="control-section">
                <div class="station-header">
                    <h4 class="mb-3">Stations</h4>
                    <a href="/manage_stations" class="btn btn-sm btn-primary">Manage Stations</a>
                </div>
                <div class="d-flex flex-wrap">
                    {% for station in preset_stations %}
                        <div class="station-container me-2 mb-2">
                            <form method="POST" action="/preset_play" class="d-inline">
                                <input type="hidden" name="uri" value="{{ station.uri }}">
                                <input type="hidden" name="name" value="{{ station.name }}">
                                <button type="submit" class="btn btn-outline-primary station-btn">{{ station.name }}</button>
                            </form>
                        </div>
                    {% endfor %}
                </div>
                
                <div class="d-flex mt-4">
                    <form method="POST" action="/play"><button class="btn btn-success">▶️</button></form>
                    <form method="POST" action="/pause"><button class="btn btn-warning">⏸</button></form>
                    <form method="POST" action="/stop"><button class="btn btn-danger">⏹</button></form>
                    <form method="POST" action="/poweroff"><button class="btn btn-dark">⏻</button></form>
                </div>
            </div>
        </div>
        
        <!-- Volume Section -->
        <div class="col-md-4">
            <div class="control-section">
                <h4 class="mb-3">Volume</h4>
                <form method="POST" action="/setvolume" id="volumeForm">
                    <div class="volume-container">
                        <input type="range" class="form-range" id="volumeSlider" name="level" min="0" max="100" value="{{ current_volume }}" oninput="updateVolumeDisplay(this.value)">
                        <div class="volume-display" id="volumeDisplay">{{ current_volume }}%</div>
                    </div>
                    <button type="submit" class="btn btn-info mt-2">Set Volume</button>
                </form>
            </div>
        </div>
    </div>
</div>

<button id="themeToggle" class="btn theme-toggle btn-light">
    <span id="themeIcon">🌙</span>
</button>

<script>
function updateVolumeDisplay(value) {
    document.getElementById('volumeDisplay').textContent = value + '%';
}

function saveStation() {
    const name = document.getElementById('stationName').value;
    const uri = document.getElementById('uri_input').value;
    
    if (!name || !uri) {
        alert('Please enter both station name and URL');
        return;
    }
    
    fetch('/save_station', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: name, uri: uri })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Station saved successfully!');
            // Reload the page without changing the URL in browser
            fetch(window.location.pathname)
                .then(response => response.text())
                .then(html => {
                    document.open();
                    document.write(html);
                    document.close();
                    history.pushState({}, '', window.location.pathname);
                });
        } else {
            alert('Error saving station: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while saving the station');
    });
}

// Toggle dark/light mode
document.getElementById('themeToggle').addEventListener('click', function() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    
    // Update theme button
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    
    if (isDarkMode) {
        themeToggle.classList.remove('btn-light');
        themeToggle.classList.add('btn-dark');
        themeIcon.textContent = '☀️';
        localStorage.setItem('theme', 'dark');
    } else {
        themeToggle.classList.remove('btn-dark');
        themeToggle.classList.add('btn-light');
        themeIcon.textContent = '🌙';
        localStorage.setItem('theme', 'light');
    }
});

// Function to handle form submissions without page navigation
document.addEventListener('DOMContentLoaded', function() {
    // Attach to all forms
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            fetch(form.action, {
                method: form.method,
                body: new FormData(form)
            })
            .then(response => response.text())
            .then(html => {
                document.open();
                document.write(html);
                document.close();
                history.pushState({}, '', window.location.pathname);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = document.getElementById('themeIcon');
        themeToggle.classList.remove('btn-light');
        themeToggle.classList.add('btn-dark');
        themeIcon.textContent = '☀️';
    }
});
</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    status = get_status()
    current_volume = get_volume()
    return render_template_string(
        TEMPLATE, 
        status=status, 
        current_volume=current_volume,
        preset_stations=PRESET_STATIONS,
        current_station=request.args.get('station', '')
    )

@app.route("/seturi", methods=["POST"])
def seturi():
    uri = request.form.get("uri")
    set_uri(uri)
    # Get status after setting the URI
    status = get_status()
    current_volume = get_volume()
    return render_template_string(
        TEMPLATE, 
        status=status, 
        current_volume=current_volume,
        preset_stations=PRESET_STATIONS,
        current_station="Custom URL"
    )

@app.route("/save_station", methods=["POST"])
def save_station():
    global PRESET_STATIONS
    
    try:
        data = request.json
        name = data.get('name')
        uri = data.get('uri')
        
        if not name or not uri:
            return jsonify({"success": False, "message": "Name and URI are required"})
        
        # Load current stations
        stations = PRESET_STATIONS.copy()
        
        # Check if station with same name already exists
        for i, station in enumerate(stations):
            if station['name'] == name:
                # Update existing station
                stations[i] = {"name": name, "uri": uri}
                break
        else:
            # Add new station
            stations.append({"name": name, "uri": uri})
        
        # Save updated stations
        if save_stations(stations):
            # Update global stations list
            PRESET_STATIONS = stations
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Failed to save station"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/preset_play", methods=["POST"])
def preset_play():
    uri = request.form.get("uri")
    station_name = request.form.get("name")
    set_uri(uri)
    play()
    # Get status after playing the preset
    status = get_status()
    current_volume = get_volume()
    return render_template_string(
        TEMPLATE, 
        status=status, 
        current_volume=current_volume,
        preset_stations=PRESET_STATIONS,
        current_station=station_name
    )

@app.route("/play", methods=["POST"])
def play_route():
    play()
    # Get status after playing
    status = get_status()
    current_volume = get_volume()
    return render_template_string(
        TEMPLATE, 
        status=status, 
        current_volume=current_volume,
        preset_stations=PRESET_STATIONS,
        current_station=request.args.get('station', '')
    )

@app.route("/pause", methods=["POST"])
def pause_route():
    pause()
    # Get status after pausing
    status = get_status()
    current_volume = get_volume()
    return render_template_string(
        TEMPLATE, 
        status=status, 
        current_volume=current_volume,
        preset_stations=PRESET_STATIONS,
        current_station=request.args.get('station', '')
    )

@app.route("/stop", methods=["POST"])
def stop_route():
    stop()
    # Get status after stopping
    status = get_status()
    current_volume = get_volume()
    return render_template_string(
        TEMPLATE, 
        status=status, 
        current_volume=current_volume,
        preset_stations=PRESET_STATIONS,
        current_station=request.args.get('station', '')
    )

@app.route("/status", methods=["GET"])
def status_route():
    status = get_status()
    current_volume = get_volume()
    return render_template_string(
        TEMPLATE, 
        status=status, 
        current_volume=current_volume,
        preset_stations=PRESET_STATIONS,
        current_station=request.args.get('station', '')
    )

@app.route("/setvolume", methods=["POST"])
def setvolume_route():
    level = request.form.get("level")
    if level:
        set_volume(level)
    # Get status after setting volume
    status = get_status()
    current_volume = level
    return render_template_string(
        TEMPLATE, 
        status=status, 
        current_volume=current_volume,
        preset_stations=PRESET_STATIONS,
        current_station=request.args.get('station', '')
    )

@app.route("/poweroff", methods=["POST"])
def poweroff_route():
    power_off()
    # Get status after powering off
    status = get_status()
    current_volume = get_volume()
    return render_template_string(
        TEMPLATE, 
        status=status, 
        current_volume=current_volume,
        preset_stations=PRESET_STATIONS,
        current_station=request.args.get('station', '')
    )

@app.route("/remove_station", methods=["POST"])
def remove_station():
    global PRESET_STATIONS
    
    try:
        name = request.form.get("name")
        
        if not name:
            return render_template_string(TEMPLATE, status=get_status(), 
                                        current_volume=get_volume(), 
                                        preset_stations=PRESET_STATIONS)
        
        # Filter out the station with the given name
        stations = [s for s in PRESET_STATIONS if s['name'] != name]
        
        # Save updated stations
        if save_stations(stations):
            # Update global stations list
            PRESET_STATIONS = stations
        
        # Get status after removing the station
        status = get_status()
        current_volume = get_volume()
        return render_template_string(
            TEMPLATE, 
            status=status, 
            current_volume=current_volume,
            preset_stations=PRESET_STATIONS,
            current_station=request.args.get('station', '')
        )
    
    except Exception as e:
        return render_template_string(TEMPLATE, status={"Error": str(e)}, 
                                      current_volume=get_volume(), 
                                      preset_stations=PRESET_STATIONS)

@app.route("/manage_stations", methods=["GET"])
def manage_stations():
    MANAGE_STATIONS_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Manage Stations</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            :root {
                --bg-color: #f8f9fa;
                --text-color: #212529;
                --card-bg: #ffffff;
                --control-bg: #f8f9fa;
                --border-color: #dee2e6;
            }
            
            .dark-mode {
                --bg-color: #121212;
                --text-color: #e0e0e0;
                --card-bg: #1e1e1e;
                --control-bg: #2a2a2a;
                --border-color: #444444;
            }
            
            body {
                background-color: var(--bg-color);
                color: var(--text-color);
                transition: background-color 0.3s, color 0.3s;
            }
            
            .container {
                max-width: 800px;
                margin-top: 50px;
            }
            
            .card {
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                background-color: var(--card-bg);
                border-color: var(--border-color);
            }
            
            .list-group-item {
                background-color: var(--card-bg);
                color: var(--text-color);
                border-color: var(--border-color);
            }
            
            .station-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .station-actions {
                display: flex;
                gap: 5px;
            }
            
            .theme-toggle {
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 1000;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card mb-4">
                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                    <h4 class="mb-0">Manage Stations</h4>
                    <div>
                        <button type="button" class="btn btn-danger" id="deleteSelectedBtn" disabled>Delete Selected</button>
                    </div>
                </div>
                <div class="card-body">
                    <ul class="list-group list-group-flush">
                        {% for station in stations %}
                        <li class="list-group-item station-item">
                            <div class="d-flex align-items-center">
                                <input type="checkbox" class="station-checkbox form-check-input me-2" value="{{ station.name }}">
                                <span>{{ station.name }}</span>
                                <small class="text-muted ms-2">{{ station.uri }}</small>
                            </div>
                            <div class="station-actions">
                                <form method="POST" action="/remove_station" class="single-delete">
                                    <input type="hidden" name="name" value="{{ station.name }}">
                                    <button type="submit" class="btn btn-sm btn-outline-danger">Delete</button>
                                </form>
                            </div>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h4 class="mb-0">Add New Station</h4>
                </div>
                <div class="card-body">
                    <form id="addStationForm" method="POST" action="/add_station">
                        <div class="mb-3">
                            <label for="stationName" class="form-label">Station Name</label>
                            <input type="text" class="form-control" id="stationName" name="name" required>
                        </div>
                        <div class="mb-3">
                            <label for="stationUri" class="form-label">Stream URL</label>
                            <input type="text" class="form-control" id="stationUri" name="uri" required>
                        </div>
                        <div class="d-flex justify-content-between">
                            <a href="/" class="btn btn-secondary">Back to Dashboard</a>
                            <button type="submit" class="btn btn-success">Add Station</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <button id="themeToggle" class="btn theme-toggle btn-light">
            <span id="themeIcon">🌙</span>
        </button>
        
        <script>
            // Check for saved theme preference
            document.addEventListener('DOMContentLoaded', function() {
                const savedTheme = localStorage.getItem('theme');
                if (savedTheme === 'dark') {
                    document.body.classList.add('dark-mode');
                    const themeToggle = document.getElementById('themeToggle');
                    const themeIcon = document.getElementById('themeIcon');
                    themeToggle.classList.remove('btn-light');
                    themeToggle.classList.add('btn-dark');
                    themeIcon.textContent = '☀️';
                }
                
                // Handle checkbox selection
                const checkboxes = document.querySelectorAll('.station-checkbox');
                const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
                
                checkboxes.forEach(checkbox => {
                    checkbox.addEventListener('change', updateDeleteButton);
                });
                
                function updateDeleteButton() {
                    const selectedCount = document.querySelectorAll('.station-checkbox:checked').length;
                    deleteSelectedBtn.disabled = selectedCount === 0;
                    deleteSelectedBtn.textContent = `Delete Selected (${selectedCount})`;
                }
                
                // Handle delete selected button
                deleteSelectedBtn.addEventListener('click', function() {
                    const selected = [];
                    document.querySelectorAll('.station-checkbox:checked').forEach(cb => {
                        selected.push(cb.value);
                    });
                    
                    if (selected.length === 0) {
                        alert('Please select at least one station to delete');
                        return;
                    }
                    
                    if (confirm(`Are you sure you want to delete ${selected.length} station(s)?`)) {
                        fetch('/remove_multiple_stations', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ names: selected })
                        })
                        .then(response => {
                            if (response.ok) {
                                window.location.reload();
                            } else {
                                throw new Error('Failed to delete stations');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('An error occurred while deleting stations');
                        });
                    }
                });
                
                // Handle form submissions without navigation
                document.querySelectorAll('.single-delete').forEach(form => {
                    form.addEventListener('submit', function(e) {
                        e.preventDefault();
                        
                        if (confirm('Are you sure you want to delete this station?')) {
                            fetch(form.action, {
                                method: form.method,
                                body: new FormData(form)
                            })
                            .then(response => {
                                window.location.reload();
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                alert('An error occurred while deleting the station');
                            });
                        }
                    });
                });
                
                // Handle add station form submission
                document.getElementById('addStationForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const form = this;
                    const formData = new FormData(form);
                    
                    fetch(form.action, {
                        method: form.method,
                        body: formData
                    })
                    .then(response => {
                        if (response.ok) {
                            alert('Station added successfully!');
                            window.location.reload();
                        } else {
                            throw new Error('Failed to add station');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred while adding the station');
                    });
                });
                
                // Toggle dark/light mode
                document.getElementById('themeToggle').addEventListener('click', function() {
                    document.body.classList.toggle('dark-mode');
                    const isDarkMode = document.body.classList.contains('dark-mode');
                    
                    // Update theme button
                    const themeToggle = document.getElementById('themeToggle');
                    const themeIcon = document.getElementById('themeIcon');
                    
                    if (isDarkMode) {
                        themeToggle.classList.remove('btn-light');
                        themeToggle.classList.add('btn-dark');
                        themeIcon.textContent = '☀️';
                        localStorage.setItem('theme', 'dark');
                    } else {
                        themeToggle.classList.remove('btn-dark');
                        themeToggle.classList.add('btn-light');
                        themeIcon.textContent = '🌙';
                        localStorage.setItem('theme', 'light');
                    }
                });
            });
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return render_template_string(MANAGE_STATIONS_TEMPLATE, stations=PRESET_STATIONS)

@app.route("/remove_multiple_stations", methods=["POST"])
def remove_multiple_stations():
    global PRESET_STATIONS
    
    try:
        data = request.json
        names = data.get('names', [])
        
        if not names:
            return jsonify({"success": False, "message": "No station names provided"}), 400
        
        # Filter out the stations with the given names
        stations = [s for s in PRESET_STATIONS if s['name'] not in names]
        
        # Save updated stations
        if save_stations(stations):
            # Update global stations list
            PRESET_STATIONS = stations
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "message": "Failed to save stations"}), 500
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/add_station", methods=["POST"])
def add_station():
    global PRESET_STATIONS
    
    try:
        name = request.form.get("name")
        uri = request.form.get("uri")
        
        if not name or not uri:
            return redirect(url_for("add_station_form"))
        
        # Load current stations
        stations = PRESET_STATIONS.copy()
        
        # Check if station with same name already exists
        for i, station in enumerate(stations):
            if station['name'] == name:
                # Update existing station
                stations[i] = {"name": name, "uri": uri}
                break
        else:
            # Add new station
            stations.append({"name": name, "uri": uri})
        
        # Save updated stations
        if save_stations(stations):
            # Update global stations list
            PRESET_STATIONS = stations
        
        return redirect(url_for("index"))
    
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True, port=5050, host="0.0.0.0")