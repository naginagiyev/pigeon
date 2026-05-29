<p align="center">
  <img src="assets/banner.jpg" alt="Pigeon — share files on your local network" width="100%">
</p>

<h1 align="center">Pigeon</h1>

<p align="center">
  Send and receive files with people on the same Wi‑Fi or LAN — no cloud, no account, no upload limits from a third party.
</p>

---

## What is Pigeon?

**Pigeon** is a small desktop app for **Windows**. It helps you **share files on your local network** (LAN). Everyone who runs Pigeon on the same network can see shared files and download them directly from each other’s computers.

- Files stay on your machine until someone downloads them.
- No internet upload is required for sharing (only your local network).

---

## How it works (simple overview)

1. **You share files** — Add files in the center panel. Pigeon keeps a list of what you are sharing.
2. **Pigeon announces itself** — Every few seconds, your app sends a short message on the local network (UDP broadcast) with your nickname, address, and file list.
3. **Others listen** — Other copies of Pigeon hear that message and show your files in the left panel.
4. **Someone downloads** — When they click download, Pigeon opens a direct connection (TCP) to your computer and copies the file in chunks.

```text
  Your PC                         Other PC
  ┌─────────┐   UDP broadcast     ┌─────────┐
  │ Pigeon  │ ──────────────────► │ Pigeon  │  "Here are my files"
  └─────────┘                     └─────────┘
       │                                │
       │         TCP file transfer      │
       └──────────────────────────────► │
```

---

## Requirements

- **Windows** 10 or later (the app is built and tested for Windows).
- **Python 3.10+** (only if you run from source).
- **Same local network** — All devices should be on the same Wi‑Fi or wired LAN.
- **Firewall** — Windows may ask to allow Pigeon on private networks; allow it so others can connect.

---

## Quick start

### Option A — Download the Windows build

Download Pigeon from my website: [products page](file:///C:/Users/nagin/OneDrive/Belgeler/Projects/Personal%20Website/products.html)

1. Download **Pigeon.exe**.
2. Double‑click **Pigeon.exe**.
3. Allow network access when the firewall asks.

### Option B — Run from source

1. **Clone or copy** this project to your computer.

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Start the app**:

   ```bash
   python app.py
   ```

---

## Using the app

The window has three areas:

### Left panel — Files on the network

- Lists files shared by **you** and **others**, newest first.
- **↓** — Download a file (you will choose where to save it).
- **✕** — Cancel an active download, or stop sharing your own file.
- Shows **progress** (percent) while a download is running.

### Center panel — Share your files

- **Drag and drop** files onto the box, or **click** to pick files.

### Right panel — Your nickname

- Open **Herald** and type a name (max 20 characters, **no spaces**).
- Press Enter or click away to save. Others see this name instead of your IP address.
- On first run, Pigeon may assign a random name like `Pigeon3847`.

---

## Settings and data

- **Config file**: `%APPDATA%\Pigeon\lanshare.config.json`
  - Stores your nickname.

---

## Project structure

```text
Pigeon/
├── app.py              # Application entry point
├── requirements.txt    # Python dependencies (PyQt6)
├── assets/
│   ├── banner.jpg      # README banner image
│   └── logo.ico        # App icon
├── core/
│   ├── discovery.py    # UDP peer discovery
│   ├── server.py       # TCP file server
│   ├── downloader.py   # Download manager
│   ├── sharedfiles.py  # Shared file registry
│   └── registry.py     # Online peers and timeouts
└── ui/
    ├── mainwindow.py   # Main window layout
    ├── leftpanel.py    # File list
    ├── centerpanel.py  # Drag-and-drop sharing
    ├── rightpanel.py   # Nickname editor
    ├── toast.py        # Notification toasts
    └── signals.py      # Qt signals between parts
```

---

## Tips and limits

- **Same network only** — Pigeon does not work across the public internet by default.
- **VPNs** — Some VPNs block local discovery; turn off VPN or allow local traffic if peers do not appear.
- **One instance per PC** — Starting a second copy may fail because port 50002 is already in use.
- **File paths** — Do not move or delete a file while you are still sharing it; remove it from the list first.

---

## Technology

- **Python 3** with **PyQt6** for the interface
- **UDP** for discovery and announcements
- **TCP** for reliable file transfer