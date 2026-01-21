# Python Automation & Computer Vision Bot 🤖
Autonomous game agent using Tesseract OCR, MVC Architecture, and ETL pipelines for real-time strategy.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green.svg)](https://opencv.org/)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An advanced, autonomous bot for Tibianic-like Pokémon MMORPGs, built with **Python**, **OpenCV**, and **Tesseract OCR**. This project demonstrates the power of computer vision and state machine logic for game automation.

> **Disclaimer:** This project is for **educational and research purposes only**. Use it at your own risk. The author is not responsible for any bans or penalties incurred while using this software.

---

## 🚀 Features

*   **Autonomous Navigation**: Detects "Goto" buttons and mission prompts to navigate automatically.
*   **Intelligent Battle System**:
    *   Reads enemy names and your own Pokémon/HP via OCR.
    *   Makes smart decisions (Fight vs. Flee) based on type advantages.
    *   Calculates damage multipliers (STAB, effectiveness).
*   **Computer Vision (Perception)**:
    *   Real-time screen capture using `mss`.
    *   State detection (Exploring, Battling, Dialog).
    *   Shiny Pokémon detection with audible alarms.
*   **OCR Integration**: Uses Tesseract to read game text (names, levels, chat).
*   **Configurable**: Highly customizable behavior via `config/settings.yaml`.

## 🛠️ Technologies

*   **[Python](https://www.python.org/)**: Core logic and control.
*   **[OpenCV](https://opencv.org/)**: Image processing and template matching.
*   **[Tesseract OCR](https://github.com/tesseract-ocr/tesseract)**: Optical Character Recognition for reading text.
*   **[MSS](https://python-mss.readthedocs.io/)**: Ultra-fast cross-platform screen capture.
*   **[PyAutoGUI](https://pyautogui.readthedocs.io/)**: Simulating mouse and keyboard actions.
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

## 🎮 Usage

1.  **Launch the Game Client** and ensure it is visible on the screen.
2.  **Run the Bot:**
    ```bash
    python run_bot.py
    ```
3.  **Controls:**
    *   The bot will start capturing the screen and logging actions.
    *   **Stop**: Press `Ctrl+C` in the terminal to stop the bot gracefully.

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
