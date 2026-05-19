# Grid Guard: DC Fault Detection System with Edge AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![TensorFlow 2.15](https://img.shields.io/badge/TensorFlow-2.15%20-%23FF6F00.svg)](https://www.tensorflow.org/)
[![ESP32](https://img.shields.io/badge/ESP32-Supported-%234285F4.svg)](https://www.espressif.com/en/products/socs/esp32)

## Overview

**Grid Guard** is an intelligent DC fault detection system that combines edge AI with real-time monitoring to protect electrical infrastructure. The system uses an ESP32 microcontroller for current sensing and relay control, streaming data to a host PC that runs a quantized TensorFlow Lite model for fault classification. When a fault is detected, the system automatically isolates the affected circuit and sends alerts via Telegram.

## Key Features

- **Real-time Fault Detection**: Identifies Open Circuit, Short Circuit, and Line-to-Ground faults with >95% accuracy
- **Automatic Isolation**: Instantly trips relay to isolate faulty sections upon detection
- **Edge AI Processing**: Lightweight TensorFlow Lite model (<100KB) runs efficiently on host PC
- **Remote Alerts**: Instant Telegram notifications with fault type, probability, and location
- **Self-Healing**: Automatically restores power after fault condition clears
- **Configurable Thresholds**: Adjustable sensitivity and timing parameters
- **Data Collection**: Built-in tools for gathering labeled training data

## System Architecture

```
┌─────────────────┐    Serial    ┌──────────────────┐   TCP/IP   ┌─────────────────┐
│   ESP32 Node    │◄────────────►│   Host PC        │◄──────────►│  Telegram Bot   │
│ (ACS712 Sensor) │   115200 baud│ (Python/TFLite)  │            │   Notifications │
│   - Current     │              │ - Model Inference│            │                 │
│   - Relay Ctrl  │              │ - Alert System   │            │                 │
└─────────────────┘              └──────────────────┘            └─────────────────┘
```

## Hardware Requirements

- **ESP32 Development Board** (e.g., ESP32 DevKitC)
- **ACS712 Current Sensor** (±5A or ±20A range)
- **5V Relay Module** (SPDT, opto-isolated preferred)
- **Jumper Wires** and **Breadboard**
- **Host Computer** with Python 3.8+ installed
- **USB Cable** for ESP32-PC communication

## Software Dependencies

### Python Packages
```bash
tensorflow==2.15.0
numpy==1.26.4
pandas==2.2.1
scikit-learn==1.4.1.post1
pyserial==3.5
requests==2.31.0
python-dotenv==1.0.1
```

### Arduino Libraries
- ACS712 (by Martin Lorton)

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Grid_Guard.git
cd Grid_Guard
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Telegram credentials:
```env
BOT_TOKEN=your_telegram_bot_token_here
CHAT_ID=your_telegram_chat_id_here
```

### 4. Flash ESP32 Firmware
1. Open `firmware/esp32_node/esp32_node.ino` in Arduino IDE
2. Select your ESP32 board and port
3. Click Upload

### 5. Verify Serial Port
Update the `PORT` variable in:
- `src/main.py`
- `src/collect_data.py`

## Usage

### Data Collection (Optional)
To gather training data for different fault conditions:
```bash
python src/collect_data.py
```
Follow the prompts to label data as:
- `0`: Normal
- `1`: Open Circuit / Line Fault
- `2`: Short Circuit
- `3`: Line-to-Ground Fault

### Model Training
```bash
python src/train_model.py
```
This will:
1. Load collected data from `data.npy` and `labels.npy`
2. Train a Conv1D neural network
3. Convert to TensorFlow Lite format (`dc_fault_model_v3.tflite`)
4. Save the model to the `models/` directory

### Real-time Monitoring
```bash
python src/main.py
```
The system will:
1. Load the TFLite model
2. Begin reading current data from ESP32
3. Classify faults in real-time
4. Automatically isolate faults via relay control
5. Send Telegram alerts for detected faults
6. Restore power after fault clearance

## Model Details

- **Architecture**: 3-layer Conv1D with BatchNormalization
- **Input**: 50-sample sequences of current measurements
- **Output**: 4-class classification (Normal, Open, Short, Ground Fault)
- **Size**: ~85 KB (quantized for efficiency)
- **Accuracy**: >95% on test dataset
- **Inference Time**: <2ms per sample on modern CPUs

## Fault Types

| Class | Type | Description |
|-------|------|-------------|
| 0 | Normal | Standard operating conditions |
| 1 | Open Circuit | Broken conductor or disconnected load |
| 2 | Short Circuit | Low-resistance path between lines |
| 3 | Line-to-Ground | Insulation failure to ground/earth |

## Configuration Parameters

Adjust these in `src/main.py` to tune system behavior:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `PORT` | ESP32 serial port | `COM7` |
| `BAUD` | Serial communication speed | `115200` |
| `SEQ_LEN` | Sequence length for model input | `50` |
| `THRESHOLD` | Classification confidence threshold | `0.5` |
| `CURRENT_DEADBAND` | Current ignore threshold (A) | `0.060` |
| `STABLE_NORMAL_SEC` | Seconds of normal state before restore | `3` |
| `RELAY_RESTORE_DELAY` | Extra delay before relay restore (s) | `3` |

## Safety Features

1. **Deadband Filtering**: Ignores noise below configurable current threshold
2. **State Machine**: Prevents rapid relay cycling with hysteresis
3. **Relay State Tracking**: Avoids false positives when relay is open
4. **Minimum Normal Period**: Ensures fault is truly cleared before restoring power
5. **Watchdog Timer**: Automatic recovery from communication loss

## Data Format

### Serial Communication
ESP32 sends raw current measurements (float, 3 decimal places):
```
0.125
-0.034
1.250
```

### Collected Data CSV
```
Timestamp,Current_A,Label
2026-05-07 10:30:15,0.125,0
2026-05-07 10:30:16,0.132,0
2026-05-07 10:30:17,0.002,1
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- TensorFlow Lite team for edge-optimized ML tools
- Arduino community for ESP32 support
- Open-source sensor libraries (ACS712)
- All contributors to the Grid Guard project

---

**Grid Guard** - Protecting electrical infrastructure with intelligent edge AI.