# Python Automation & Computer Vision Bot 🤖
Autonomous game agent using Tesseract OCR, MVC Architecture, and ETL pipelines for real-time strategy.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![Tesseract](https://img.shields.io/badge/Tesseract-OCR-green?logo=google&logoColor=white)](https://github.com/tesseract-ocr/tesseract)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()

An advanced, autonomous bot for Tibianic-like Pokémon MMORPGs, built with **Python**, **OpenCV**, and **Tesseract OCR**. This project demonstrates the power of computer vision and state machine logic for game automation.

> **Disclaimer:** This project is for **educational and research purposes only**. Use it at your own risk. The author is not responsible for any bans or penalties incurred while using this software.

---

## 🚀 Features

### 🎯 Core Features
*   **Autonomous Navigation**: Detects "Goto" buttons and mission prompts to navigate automatically.
*   **Intelligent Battle System**:
    *   Reads enemy names and your own Pokémon/HP via OCR.
    *   Makes smart decisions (Fight vs. Flee) based on type advantages.
    *   Calculates damage multipliers (**STAB**, effectiveness).
    *   Detects HP levels and recommends healing/switching.
*   **Computer Vision (Perception)**:
    *   Real-time screen capture using `mss`.
    *   State detection (Exploring, Battling, Dialog).
    *   Shiny Pokémon detection with audible alarms.
*   **OCR Integration**: Uses Tesseract to read game text (names, levels, chat).
*   **Configurable**: Highly customizable behavior via `config/settings.yaml`.

### 🤖 Humanization Features (v2.0)
*   **Bezier Curve Movements**: Mouse moves in natural curves, not straight lines
*   **Randomized Delays**: Variable timing (50-500ms) prevents pattern detection
*   **Idle Actions**: Occasional camera movement, spacebar presses, and pauses
*   **AI Chat Integration** (Optional): Natural conversation using Ollama/Gemini/OpenAI
*   **HP Detection**: Color-based analysis of HP bars for intelligent item/switch decisions

### 🎮 State Machine System (v2.1)
*   **4 Operational Modes**:
    *   **IDLE**: Passive observation (only alerts on Shiny)
    *   **MISSION**: Automated quest progression (follows Goto/Talk)
    *   **HUNTING**: Targeted Pokémon hunting (flees from non-targets)
    *   **FOLLOW**: Tracks and follows your main character (for secondary accounts)
*   **Priority System**: Shiny > Battle > Behavior
*   **Smart Hunting**: Automatically flees from unwanted encounters

### 🎮 Hotkey Control System (v2.2)
*   **Real-Time Control**: Switch modes instantly without restarting the bot
*   **Global Hotkeys**: Works even when game window is focused (F1-F9)
*   **Pause/Resume**: Freeze bot temporarily with a single key press
*   **Follow Mode**: 
    *   Template matching to visually track your character
    *   Party button support for automatic following
    *   Configurable distance and detection thresholds
*   **30-60x Faster**: Change modes in ~1 second vs ~30-60 seconds before!

### 🌐 Remote Control via UDP (v2.3)
*   **VM Control**: Control bot running in VM from your physical machine
*   **Ultra-Low Latency**: 1-5ms response time (UDP protocol)
*   **No RDP Required**: Send commands without opening VM console
*   **Multi-VM Support**: Control multiple VMs simultaneously from one host
*   **Simple Setup**: Just open 1 UDP port and configure IP
*   **Background Operation**: Works even when VM is minimized

### 🧠 Advanced AI & Follow Intelligence (v2.4)
*   **Dynamic HP Detection**: 
    *   Color-based HP analysis (HSV color space)
    *   **10-40x faster** than OCR (5-10ms vs 50-200ms)
    *   Detects green/yellow/red HP bars
*   **Persistent Follow Mode**:
    *   **OCR Name Tracking**: Finds player by in-game username
    *   **Memory System**: Remembers last seen position (5s timeout)
    *   **Recovery Search**: Automatically rotates camera/moves to reacquire lost targets
    *   **Smart Movement**: 70% proportional movement prevents vibration
*   **Battle Intelligence**:
    *   HP-based healing decisions (< 25% HP)
    *   Automatic Pokémon switching when HP critical
    *   Type advantage calculations with STAB bonus

### ⚔️ Advanced Battle Engine (v2.5) ⭐ NEW!
*   **Risk/Reward Analysis**:
    *   Projects next turn to prevent suicidal plays
    *   Calculates if you'll survive before attacking
    *   Smart healing: only heals when safe
*   **Damage Prediction System**:
    *   Estimates incoming enemy damage
    *   Factors type effectiveness & enemy items
    *   Auto-switches when death is imminent
*   **Item Inference (AI)**:
    *   **Detects Choice Scarf** automatically (speed-based)
    *   **Detects Choice Band/Life Orb** (damage-based)
    *   Adjusts strategy mid-battle based on inference
*   **Speed Tier Calculations**:
    *   Real Pokémon formula (IVs, EVs, Nature)
    *   Predicts who attacks first
    *   Considers worst-case scenarios


## 🛠️ Technologies

*   **[Python](https://www.python.org/)**: Core logic and control.
*   **[OpenCV](https://opencv.org/)**: Image processing and template matching.
*   **[Tesseract OCR](https://github.com/tesseract-ocr/tesseract)**: Optical Character Recognition for reading text.
*   **[MSS](https://python-mss.readthedocs.io/)**: Ultra-fast cross-platform screen capture.
*   **[PyAutoGUI](https://pyautogui.readthedocs.io/)**: Simulating mouse and keyboard actions.
*   **[SciPy](https://scipy.org/)**: Bezier curve calculations for human-like movements.
*   **[Pynput](https://pynput.readthedocs.io/)**: Global hotkey listener for real-time control.
*   **[Loguru](https://github.com/Delgan/loguru)**: Pleasant execution logging.

## 📋 Prerequisites

1.  **Windows OS** (Required for `winsound` alerts and specific input handling).
2.  **Python 3.8+** installed.
3.  **Tesseract OCR** installed:
    *   Download and install from [UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki).
    *   Ensure the installation path matches the one in your `config/settings.yaml` (default: `C:\Program Files\Tesseract-OCR\tesseract.exe`).

## ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Fesisp/PokeBot.git
    cd PokeBot
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Tesseract:**
    Open `config/settings.yaml` and verify the `ocr.tesseract_cmd` path points to your local Tesseract executable.

## 🎮 Quick Start

### Basic Usage

1.  **Launch the Game Client** and ensure it is visible on the screen.
2.  **Run the Bot:**
    ```bash
    python run_bot.py
    ```
3.  **Controls:**
    *   The bot will display available hotkeys on startup
    *   **F1-F4**: Switch between modes instantly
    *   **F5/F6**: Pause/Resume bot
    *   **F9**: Stop bot completely
    *   **Ctrl+C** (terminal): Alternative way to stop

### Real-Time Control (NEW! v2.2)

**No need to restart the bot anymore!** Use hotkeys to control in real-time:

| Hotkey | Action |
|--------|--------|
| **F1** | Switch to IDLE mode |
| **F2** | Switch to MISSION mode |
| **F3** | Switch to HUNTING mode |
| **F4** | Switch to FOLLOW mode |
| **F5** | Pause bot |
| **F6** | Resume bot |
| **F9** | Stop bot |

**Example workflow:**
```
1. Start bot: python run_bot.py
2. Press F2 → Bot starts doing missions
3. Press F5 → Bot pauses (you take control)
4. Press F6 → Bot resumes
5. Press F3 → Bot switches to hunting mode
6. Press F9 → Bot stops
```

All in **~1 second each** - no more editing configs and restarting!

### Choosing a Mode (Configuration)

You can also set the initial mode in `config/settings.yaml`:

**Mission Mode (Default)** - Automated quest progression:
```yaml
bot:
  behavior: "mission"
```

**Hunting Mode** - Target specific Pokémon:
```yaml
bot:
  behavior: "hunting"

hunt:
  target_pokemon: ["ditto", "eevee"]
  move_interval: 2.0
```

**Follow Mode** - Track and follow your main character:
```yaml
bot:
  behavior: "follow"

follow:
  method: "template"  # or "party_button"
  player_template: "player_char.png"
  match_threshold: 0.7
```

**Idle Mode** - Passive Shiny detection only:
```yaml
bot:
  behavior: "idle"
```

### 📖 Documentation

- **[🚀 Hotkey Quick Setup](docs/QUICK_SETUP_HOTKEYS.md)** - Get started with hotkeys in 5 minutes
- **[🎮 Hotkey System Guide](docs/HOTKEY_SYSTEM.md)** - Complete hotkey documentation
- **[🌐 Remote Control UDP](docs/REMOTE_CONTROL_UDP.md)** - Control bot in VM from host machine
- **[🧠 Follow Mode Guide](docs/FOLLOW_MODE_GUIDE.md)** - Advanced FOLLOW with memory and AI
- **[⚔️ Advanced Battle Engine](docs/ADVANCED_BATTLE_ENGINE.md)** - Risk calculation & damage prediction ⭐ NEW!
- **[📋 Changelog v2.4](docs/CHANGELOG_v2.4.md)** - What's new in v2.4
- **[Quick Start Guide](docs/QUICK_START.md)** - Installation and setup
- **[Modes Guide](docs/MODES_QUICK_GUIDE.md)** - How to use IDLE/MISSION/HUNTING/FOLLOW
- **[State Machine](docs/STATE_MACHINE.md)** - Technical architecture
- **[Humanization Features](docs/HUMANIZATION_FEATURES.md)** - Anti-detection features
- **[Changelog](docs/CHANGELOG.md)** - Version history and updates


## 📂 Project Structure

```
PokeBot/
├── assets/           # Template images for OpenCV matching
├── config/           # Configuration files (settings.yaml)
├── data/             # Game knowledge (Pokedex, moves, types JSONs)
├── docs/             # Documentation and design overviews
├── src/              # Source code
│   ├── action/       # Mouse/Keyboard inputs
│   ├── core/         # Main loop and bot controller
│   ├── decision/     # Battle logic and strategy
│   ├── knowledge/    # Data managers (PokeAPI, Team)
│   ├── perception/   # Vision, OCR, and state detection
│   └── utils/        # Helper functions
├── tests/            # Unit tests
└── run_bot.py        # Entry point
```

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
