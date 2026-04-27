# 5 Star Fitness — Local Setup Guide

This guide covers everything needed to run the app on a new machine.
Follow each step in order.

---

## Prerequisites

Install these before anything else:

1. **Python 3.11+** — https://www.python.org/downloads/
   - ✅ Check **"Add Python to PATH"** during installation

2. **Git** — https://git-scm.com/download/win

---

## Step 1 — Clone the project

Open Command Prompt and run:

```
git clone https://github.com/Srijan-Dawadi/GymWebApp.git
cd GymWebApp
```

---

## Step 2 — Run the setup script

Double-click **`setup.bat`** in the project folder.

This will:
- Create a virtual environment
- Install all Python dependencies
- Set up the database
- Create your admin account

---

## Step 3 — Install face recognition models

The face recognition and anti-spoofing models are **not included in the repository** (too large for GitHub). You must download and place them manually.

### 3a — buffalo_l (Face Recognition)

This downloads automatically on first use. When you first open the Attendance page and start the camera, InsightFace will download `buffalo_l` (~300MB) to:

```
C:\Users\<YourName>\.insightface\models\buffalo_l\
```

You need an internet connection the first time. After that it works offline.

### 3b — Anti-Spoofing Model (MiniFASNetV2-SE)

This must be downloaded manually.

**Download link:**
https://github.com/johnraivenolazo/face-antispoof-onnx/tree/main/models

1. Click on `best_model_quantized.onnx`
2. Click the **Download** button (or the raw file icon)
3. Save the file
4. **Rename it** to `antispoof.onnx`
5. Place it in the project at:

```
GymWebApp\static\antispoof\antispoof.onnx
```

The folder `static\antispoof\` already exists — just drop the file in.

---

## Step 4 — Start the app

Double-click **`Start GymApp.bat`** on your desktop (or in the project folder).

- The browser will open automatically at `http://localhost:8000`
- Log in with the admin credentials you set during setup

---

## Step 5 — Verify face recognition is working

1. Go to **Members** → Add a member with face enrollment (5 angles)
2. Go to **Attendance** → Start Camera
3. The member should be recognized and checked in

To test anti-spoofing: show a printed photo or phone screen to the camera — it should show **🚫 Spoof Detected** instead of checking in.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `No module named insightface` | Run `myenv\Scripts\pip install -r requirements-local.txt` |
| Camera not working | Allow camera permissions in browser |
| buffalo_l not downloading | Check internet connection, try again |
| Anti-spoof not working | Make sure `static\antispoof\antispoof.onnx` exists |
| `SECRET_KEY` error | Check that `.env` file exists in project root |

---

## File locations summary

```
GymWebApp\
├── static\
│   └── antispoof\
│       └── antispoof.onnx          ← download manually (Step 3b)
├── .env                             ← created by setup.bat
├── setup.bat                        ← run once on new machine
└── Start GymApp.bat                 ← run daily to start app

C:\Users\<YourName>\.insightface\
└── models\
    └── buffalo_l\                   ← auto-downloaded on first use
        ├── det_10g.onnx
        ├── w600k_r50.onnx
        └── ...
```
