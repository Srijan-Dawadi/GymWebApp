# 5 Star Fitness — Local Setup Guide

Follow each step in order on a new machine.

---

## Prerequisites

1. **Python 3.11+** — https://www.python.org/downloads/
   - ✅ Check **"Add Python to PATH"** during installation
2. **Git** — https://git-scm.com/download/win

---

## Step 1 — Clone the project

```
git clone https://github.com/Srijan-Dawadi/GymWebApp.git
cd GymWebApp
```

---

## Step 2 — Create virtual environment and install dependencies

```
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
```

> The face recognition packages (`insightface`, `opencv-python`) are large — this may take 3–5 minutes.

---

## Step 3 — Create the environment file

Create a `.env` file in the project root with this content:

```
SECRET_KEY=any-random-string-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Step 4 — Set up the database

```
myenv\Scripts\python manage.py migrate
myenv\Scripts\python manage.py create_superuser
```

---

## Step 5 — Download the anti-spoofing model

This model is not included in the repo (file size). Must be placed manually.

1. Download from: https://github.com/johnraivenolazo/face-antispoof-onnx/tree/main/models
2. Click `best_model_quantized.onnx` → Download
3. Rename it to `antispoof.onnx`
4. Place it at:

```
GymWebApp\static\antispoof\antispoof.onnx
```

> The `buffalo_l` face recognition model (~300MB) downloads **automatically** the first time you open the Attendance page and start the camera. Internet required for that first run only.

---

## Step 6 — Run the app

```
myenv\Scripts\python manage.py runserver
```

Open http://localhost:8000 in your browser and log in with the superuser credentials you created in Step 4.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Face recognition not available on this server` | Make sure you ran `pip install -r requirements.txt` inside the venv |
| `No module named insightface` | Same as above |
| Camera not working | Allow camera permissions in the browser |
| `buffalo_l` not downloading | Check internet connection and try again |
| Anti-spoof not working | Confirm `static\antispoof\antispoof.onnx` exists |
| `SECRET_KEY` error | Check `.env` file exists in the project root |
| `No module named environ` | Run `pip install django-environ` |

---

## File locations

```
GymWebApp\
├── static\
│   └── antispoof\
│       └── antispoof.onnx     ← download manually (Step 5)
├── .env                        ← create manually (Step 3)
└── requirements.txt            ← install with pip (Step 2)

C:\Users\<YourName>\.insightface\
└── models\
    └── buffalo_l\              ← auto-downloaded on first camera use
```
