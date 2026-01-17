# 🐍 Habbo Clientless Python Bot (Flash/Air Protocol)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) [![Discord](https://img.shields.io/badge/Discord-shuffleah-5865F2)](https://discord.com)

A fully functional, **headless (clientless)** automation framework for Habbo Hotel. This project implements the complete Flash/Air binary protocol from scratch in Python. It runs entirely via TCP sockets—**no browser, no Flash, and no AIR client required.**

Because it is clientless, you can run **100+ bots** on a single low-end VPS.

---

## 📺 Demo & Premium GUI

While this repository contains the **Open Source Core Library** (CLI), we also offer a sophisticated GUI version for managing massive bot farms.

[![Habbo Bot Demo](https://img.youtube.com/vi/WHIgTtDK14E/0.jpg)](https://www.youtube.com/watch?v=WHIgTtDK14E)

> **👆 CLICK TO WATCH:** See the bot in action performing movement, chatting, and multi-bot handling.

### 💼 Services & Contact
*   **Discord:** `shuffleah`
*   **Services:** Custom Bot Development, GUI Access, Private Exploits.
*   **Source Code:** The core logic in this repo is **free**. The GUI shown in the video is a paid add-on.

---

## ⚠️ Disclaimer
**EDUCATIONAL PURPOSES ONLY.**
This software demonstrates binary network protocols, RSA/Diffie-Hellman encryption, and socket programming. The authors are not responsible for how you use this code. Using this on official servers may result in account bans.

---

## ✨ Features

*   **⚡ Lightweight & Fast:** 100% Python. No heavy browser instances (Selenium/Puppeteer) required.
*   **🔐 Native Encryption:** Full implementation of RSA & Diffie-Hellman Handshake + RC4 Stream Cipher.
*   **🎟️ SSO Ticket Generator:** Authenticates via the Web API using browser cookies.
*   **🧠 Room Engine:** Parses `HeightMap` and `FloorMap` to detect walls, furniture, and doors.
*   **🗺️ Pathfinding:** Includes room-aware random walking (won't walk through walls).
*   **🛡️ Proxy Support:** Native SOCKS5/HTTP proxy support for IP anonymization.
*   **💬 Interactions:** Chat (Shout/Whisper), Dance, Sign, Posture, Clothes Changing.

---

## 📚 Documentation

We have comprehensive guides located in the [`/docs`](docs/) folder:

1.  **📖 [Cookbook & Examples](docs/examples.md)**
    *   *How to Walk, Dance, Chat, and Auto-Reply.*
    *   *How to use Proxies.*
    *   *How to make a "Follow Bot".*

2.  **🛠️ [Reverse Engineering & Upgrading](docs/packet_engineering.md)**
    *   *How to find new Packet IDs using G-Earth.*
    *   *How to update `constants.py` when Habbo updates.*
    *   *Resources like Sulek.dev.*

---

## 🚀 Quick Start

### 1. Installation
Requires Python 3.10 or higher.
```bash
git clone https://github.com/devlyresh/Habbo-Bot.git
cd Habbo-Bot
pip install pycryptodome requests PySocks
```
### 2. Configuration (Cookies)
To log in, the bot needs your session cookies.
1.  Login to Habbo on your browser.
2.  Press `F12` (Dev Tools) -> **Network**.
3.  Refresh the page. Filter for `clientnative`.
4.  Click the request named `url`.
5.  Copy `session.id` and `browser_token` from **Request Headers**.

Open `main.py` and paste them:
```python
MY_COOKIES = [
    {"name": "session.id", "value": "YOUR_SESSION_ID"},
    {"name": "browser_token", "value": "YOUR_BROWSER_TOKEN"}
]
```
### 3. Run

```Bash
python main.py
```

---

## 📂 Project Structure

| File | Description |
| :--- | :--- |
| `habbo_client.py` | **Core.** Handles TCP connection, Encryption, and the main Event Loop. |
| `habbo_packet.py` | **Binary.** Big-Endian packet packer/unpacker (`struct` wrapper). |
| `sso_manager.py` | **Auth.** Fetches the Login Ticket via HTTPS. |
| `constants.py` | **Config.** Packet Headers (IDs), RSA Keys, Version Strings. |
| `composers.py` | **Outgoing.** Functions to build packets (Walk, Chat, etc.). |
| `parsers.py` | **Incoming.** Functions to read packets (Users, Room Map). |
| `room_map.py` | **Physics.** Logic for collision detection and valid tiles. |

---

## 🌍 Changing Servers
By default, this is set to **US (.com)**. To change to Turkey, Brazil, or Spain:

1.  **Edit `constants.py`:**
    ```python
    HABBO_HOST = "game-tr.habbo.com" # Turkey
    # HABBO_HOST = "game-br.habbo.com" # Brazil
    ```
2.  **Edit `sso_manager.py`:**
    ```python
    BASE_HEADERS = {
        'origin': 'https://www.habbo.com.tr',
        'referer': 'https://www.habbo.com.tr/',
        # ...
    }
    ```

---

## 🤝 Contributing & Pull Requests

The Habbo protocol changes often. If you find a broken packet or add a new feature (like Pet Interaction, Trading, or Group logic), please open a **Pull Request**!

**Helpful Tools for Contributors:**
*   [G-Earth](https://github.com/sirjonasxx/G-Earth) (Packet Logger/Injector)
*   [Sulek.dev API](https://sulek.dev/api) (Packet Structure Reference)

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
