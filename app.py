import time
import threading
import subprocess
import re
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import streamlit as st
from CoreWLAN import CWWiFiClient
 
# Set up Streamlit page layout to wide mode
st.set_page_config(page_title="Wi-Fi Broadband PSD Dashboard", layout="wide")
 
# --- CHANNEL CONFIGURATION MAPPING ---
CHANNELS_24 = {1: 2412, 2: 2417, 3: 2422, 4: 2427, 5: 2432, 6: 2437, 7: 2442, 8: 2447, 9: 2452, 10: 2457, 11: 2462}
CHANNELS_5 = {36: 5180, 40: 5200, 44: 5220, 48: 5240, 52: 5260, 56: 5280, 60: 5300, 64: 5320, 
              149: 5745, 153: 5765, 157: 5785, 161: 5805, 165: 5825}
 
# Initialize session state for tracking selected band
if "current_band" not in st.session_state:
    st.session_state.current_band = "2.4 GHz"
 
# Shared memory structures for the background scanner
if "scan_data" not in st.session_state:
    st.session_state.latest_scan_data = []
    st.session_state.connected_info = {'ssid': 'Not Connected', 'rssi': -100, 'noise': -98, 'sinr': 0, 'channel': 0, 'freq': 0, 'band': 'None'}
    st.session_state.data_lock = threading.Lock()
 
def get_unredacted_connected_ssid():
    try:
        for iface in ['en0', 'en1']:
            script = f"show State:/Network/Interface/{iface}/AirPort\nd.show"
            res = subprocess.run(['scutil'], input=script, capture_output=True, text=True, timeout=1)
            match = re.search(r'SSID\s+:\s+(.+)', res.stdout)
            if match:
                name = match.group(1).strip()
                if "0x" not in name and "<data>" not in name.lower():
                    return name
    except Exception:
        pass
    return None
 
def extract_unredacted_scan_names():
    names_map = {}
    try:
        for iface in ['en0', 'en1']:
            res = subprocess.run(['networksetup', '-getairportnetwork', iface], capture_output=True, text=True, timeout=2)
            if "Current Wi-Fi Network" in res.stdout:
                scan_res = subprocess.run(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-s'], capture_output=True, text=True, timeout=4)
                for line in scan_res.stdout.split('\n')[1:]:
                    parts = line.split()
                    if len(parts) >= 4:
                        for i, part in enumerate(parts):
                            if re.match(r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$', part):
                                bssid = part.lower()
                                ssid = " ".join(parts[:i])
                                if ssid and "0x" not in ssid and "<data>" not in ssid.lower():
                                    names_map[bssid] = ssid
                                break
                if names_map:
                    return names_map
    except Exception:
        pass
    return names_map
 
def continuous_scanner(lock, state_ref):
    client = CWWiFiClient.sharedWiFiClient()
    interface = client.interface()
    while True:
        try:
            active_ssid = get_unredacted_connected_ssid()
            active_rssi = interface.rssiValue()
            active_noise = interface.noiseMeasurement() if interface.noiseMeasurement() != 0 else -98
 
            if active_ssid and active_rssi != 0 and active_rssi != -128:
                ch_obj = interface.wlanChannel()
                ch_num = ch_obj.channelNumber() if ch_obj else 0
                c_band = "2.4 GHz" if ch_num <= 14 else "5 GHz"
                c_freq = (2412 + (ch_num - 1) * 5) if ch_num <= 14 else (5000 + (ch_num * 5))
                conn = {
                    'ssid': active_ssid, 'rssi': active_rssi, 'noise': active_noise,
                    'sinr': active_rssi - active_noise, 'channel': ch_num, 'freq': c_freq, 'band': c_band
                }
            else:
                conn = {'ssid': 'Not Connected', 'rssi': -100, 'noise': -98, 'sinr': 0, 'channel': 0, 'freq': 0, 'band': 'None'}
 
            profile_names = extract_unredacted_scan_names()
            networks, error = interface.scanForNetworksWithName_error_(None, None)
 
            if networks:
                frame_data = []
                for net in networks:
                    channel_obj = net.wlanChannel()
                    if not channel_obj: continue
                    channel = channel_obj.channelNumber()
                    band_id = channel_obj.channelBand() 
                    freq = 2412 + (channel - 1) * 5 if band_id == 1 else 5000 + (channel * 5)
                    width_val = channel_obj.channelWidth() 
                    width_map = {1: 20, 2: 40, 3: 80}
                    ch_width = width_map.get(width_val, 20)
                    s_name = net.ssid()
                    net_bssid = net.bssid().lower() if net.bssid() else ""
 
                    if not s_name or "0x" in s_name or "data" in s_name.lower() or s_name.strip() == "":
                        if net_bssid in profile_names: s_name = profile_names[net_bssid]
                        elif conn['ssid'] != 'Not Connected' and channel == conn['channel']: s_name = conn['ssid']
                        else: s_name = f"Hidden_Ch{channel}_{net_bssid[-5:] if net_bssid else 'Unknown'}"
 
                    rssi = net.rssiValue()
                    noise = net.noiseMeasurement() if net.noiseMeasurement() != 0 else -98
                    integrated_psd = rssi + int(10 * np.log10(ch_width)) - 3
 
                    frame_data.append({
                        'ssid': s_name, 'channel': channel, 'freq': freq, 'width': ch_width,
                        'rssi': rssi, 'noise': noise, 'psd_band': integrated_psd, 
                        'band': "2.4 GHz" if band_id == 1 else "5 GHz"
                    })
 
                with lock:
                    state_ref['latest_scan_data'] = frame_data
                    state_ref['connected_info'] = conn
        except Exception:
            pass
        time.sleep(1.5)
 
# Start background thread tied to global execution context across runs
if "scanner_started" not in st.session_state:
    st.session_state.shared_dict = {
        'latest_scan_data': [], 
        'connected_info': {'ssid': 'Not Connected', 'rssi': -100, 'noise': -98, 'sinr': 0, 'channel': 0, 'freq': 0, 'band': 'None'}
    }
    scan_thread = threading.Thread(
        target=continuous_scanner, 
        args=(st.session_state.data_lock, st.session_state.shared_dict), 
        daemon=True
    )
    scan_thread.start()
    st.session_state.scanner_started = True
 
def draw_sharp_bandwidth_mask(x_freqs, center_freq, peak_rssi, noise_floor, ch_width):
    half_w = ch_width / 2.0
    mask = np.full_like(x_freqs, noise_floor)
    inside_mask = (x_freqs >= (center_freq - half_w)) & (x_freqs <= (center_freq + half_w))
    left_skirt = (x_freqs >= (center_freq - half_w - 2)) & (x_freqs < (center_freq - half_w))
    right_skirt = (x_freqs > (center_freq + half_w)) & (x_freqs <= (center_freq + half_w + 2))
    mask[inside_mask] = peak_rssi
    mask[left_skirt] = noise_floor + (peak_rssi - noise_floor) * ((x_freqs[left_skirt] - (center_freq - half_w - 2)) / 2)
    mask[right_skirt] = noise_floor + (peak_rssi - noise_floor) * (1.0 - ((x_freqs[right_skirt] - (center_freq + half_w)) / 2))
    return mask
 
def draw_inner_energy_hill(x_freqs, center_freq, peak_rssi, noise_floor, ch_width):
    sigma = ch_width / 3.2
    hill = (peak_rssi - 4 - noise_floor) * np.exp(-((x_freqs - center_freq) ** 2) / (2 * sigma ** 2)) + noise_floor
    inside_ch = (x_freqs >= (center_freq - (ch_width/2))) & (x_freqs <= (center_freq + (ch_width/2)))
    ripples = np.sin(x_freqs * 1.8) * 4.0 + np.cos(x_freqs * 0.9) * 2.0
    hill[inside_ch] += ripples[inside_ch]
    return np.clip(hill, noise_floor, -10)
 
def calculate_rf_sinr(target_net, all_networks):
    t_center = target_net['freq']
    t_half = target_net['width'] / 2.0
    t_min, t_max = t_center - t_half, t_center + t_half
    total_interference_mw = 10 ** (target_net['noise'] / 10.0)
    for net in all_networks:
        if net == target_net: continue
        n_center = net['freq']
        n_half = net['width'] / 2.0
        n_min, n_max = n_center - n_half, n_center + n_half
        if max(t_min, n_min) < min(t_max, n_max):
            overlap_width = min(t_max, n_max) - max(t_min, n_min)
            fraction = overlap_width / net['width']
            inter_mw = (10 ** (net['rssi'] / 10.0)) * fraction
            total_interference_mw += inter_mw
    return target_net['rssi'] - (10 * np.log10(total_interference_mw))
 
# --- STREAMLIT UI VIEW SYSTEM ---
st.title("📡 Wi-Fi Professional Broadband PSD Analysis")
 
# Select Band Buttons via native Streamlit column triggers
col1, col2, col3 = st.columns([1, 1, 5])
with col1:
    if st.button("⚡ 2.4 GHz Band", use_container_width=True):
        st.session_state.current_band = "2.4 GHz"
with col2:
    if st.button("🚀 5 GHz Band", use_container_width=True):
        st.session_state.current_band = "5 GHz"
 
# Creating dynamic placeholders to eliminate flickering on loop re-renders
graph_placeholder = st.empty()
metrics_placeholder = st.empty()
table_placeholder = st.empty()
 
cmap = plt.get_cmap('turbo')
norm = mcolors.Normalize(vmin=-98, vmax=-40)
 
# Main UI Infinite Refresh Thread Loop
while True:
    current_band = st.session_state.current_band
    with st.session_state.data_lock:
        current_snapshot = list(st.session_state.shared_dict['latest_scan_data'])
        active_conn = dict(st.session_state.shared_dict['connected_info'])
 
    if current_band == "2.4 GHz":
        freq_min, freq_max, channels = 2400, 2485, CHANNELS_24
    else:
        freq_min, freq_max, channels = 5150, 5850, CHANNELS_5
 
    x_freqs = np.arange(freq_min, freq_max, 0.2)
    base_noise_floor = -98
 
    # Set up Matplotlib Figure Object parameters
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor('#1c2024')
    ax.set_facecolor('#0d0f12')
    ax.set_title(f"Power Spectral Density Envelope ({current_band})", fontsize=11, fontweight='bold', color='white')
    ax.set_xlabel("Frequency [MHz]", fontsize=9, color='white')
    ax.set_ylabel("Amplitude [dBm]", fontsize=9, color='white')
    ax.set_xlim([freq_min, freq_max])
    ax.set_ylim([-102, -30])
    ax.grid(True, linestyle=':', color='#2c313c', alpha=0.6)
    ax.tick_params(colors='white', labelsize=8)
 
    table_rows = []
    sorted_snapshot = sorted(current_snapshot, key=lambda x: x['width'], reverse=True)
 
    for net in sorted_snapshot:
        if net['band'] == current_band:
            f_center = net['freq']
            rssi_val = net['rssi']
            w = net['width']
 
            computed_sinr = calculate_rf_sinr(net, sorted_snapshot)
            table_rows.append({
                "Network SSID": net['ssid'], "Peak RSSI": f"{rssi_val} dBm",
                "Center Freq": f"{f_center} MHz", "Channel": f"Ch {net['channel']}",
                "Integrated PSD": f"{net['psd_band']:.1f} dBm", "SINR": f"{computed_sinr:.1f} dB"
            })
 
            mask_line = draw_sharp_bandwidth_mask(x_freqs, f_center, rssi_val, base_noise_floor, ch_width=w)
            is_connected = (active_conn['ssid'] != 'Not Connected' and net['ssid'] == active_conn['ssid'] and net['channel'] == active_conn['channel'])
 
            box_color = '#00d2ff' if is_connected else ('#e67e22' if w == 40 else ('#9b59b6' if w == 80 else '#2ecc71'))
            line_w = 2.2 if is_connected else 1.0
            label_suffix = " [CONNECTED]" if is_connected else ""
 
            ax.plot(x_freqs, mask_line, color=box_color, linewidth=line_w, alpha=0.8)
            energy_hill = draw_inner_energy_hill(x_freqs, f_center, rssi_val, base_noise_floor, ch_width=w)
            ax.plot(x_freqs, energy_hill, color='#00ffff', linewidth=0.4, alpha=0.2)
 
            for y_lev in range(base_noise_floor, int(np.max(energy_hill)), 3):
                ax.fill_between(x_freqs, y_lev, y_lev + 3, where=(energy_hill >= y_lev), color=cmap(norm(y_lev)), alpha=0.12)
            ax.text(f_center, rssi_val + 1, f"{net['ssid']}{label_suffix}", fontsize=7, ha='center', va='bottom', color='white')
 
    for ch, ch_freq in channels.items():
        ax.axvline(x=ch_freq, color='#2c313c', linestyle=':', linewidth=0.7)
        ax.text(ch_freq, -33, f"{ch}", ha='center', fontsize=7.5, color='#888888')
 
    # 1. Update Graph Canvas Layout
    graph_placeholder.pyplot(fig)
    plt.close(fig)
 
    # 2. Update Dynamic Live Network Connection Status Metric Blocks
    with metrics_placeholder.container():
        if active_conn['ssid'] != 'Not Connected' and active_conn['band'] == current_band:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Connected Network", active_conn['ssid'])
            m2.metric("Channel / Frequency", f"Ch {active_conn['channel']} ({active_conn['freq']} MHz)")
            m3.metric("Signal Power (RSSI)", f"{active_conn['rssi']} dBm")
            m4.metric("Hardware SNR", f"{active_conn['sinr']} dB")
        else:
            st.info("System Link Status: Disconnected or monitoring different frequency spectrum block parameters.")
 
    # 3. Update Clean Interactive DataFrame Grid Data Layout
    if table_rows:
        sorted_table = sorted(table_rows, key=lambda x: x['Network SSID'])[:8]
        table_placeholder.dataframe(sorted_table, use_container_width=True)
    else:
        table_placeholder.warning("Waiting for background RF scan parameters data pipeline elements...")
 
    time.sleep(1.5)