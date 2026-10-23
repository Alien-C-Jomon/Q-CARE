# 🩺 Q-Care — AI-Powered Health Decision Support

**Smarter health information. Trusted medical evidence. Experimental quantum-inspired ranking.**

Q-Care is an AI-powered health decision-support project designed to help users understand health concerns, explore trusted medical information, and recognize situations that may require urgent medical attention.

By combining AI-assisted conversations, evidence retrieval, precautionary safety checks, image-based observations, and experimental quantum optimization, Q-Care explores how emerging technologies can make health information more accessible and useful.

> ⚠️ **Medical disclaimer:** Q-Care is an experimental educational project. It does not diagnose diseases, replace qualified healthcare professionals, or guarantee the accuracy of its assessments. Seek emergency medical care when necessary.

## ✨ Key Features

- 🤖 **AI-powered conversations** — Uses Google's Gemini models to explain health information conversationally.
- 🔎 **Evidence-based retrieval** — Designed to retrieve relevant information from trusted medical resources.
- 🏥 **Trusted sources** — Integrates evidence-retrieval functionality for resources such as WHO, MedlinePlus, and CDC.
- 🛡️ **Safety-first pipeline** — Includes safety checks, clinical-context classification, evidence gating, and precautionary analysis.
- 🧠 **Experimental quantum optimization** — Uses QUBO/QAOA-based evidence selection to explore ranking and selection of relevant evidence.
- 🖼️ **Image-assisted observations** — Supports image-based observations through a vision model; these observations are not medical diagnoses.
- 📊 **Evidence confidence profiling** — Evaluates evidence quality and coverage rather than claiming a medically validated probability of disease.
- 🌐 **Web interface** — Provides a frontend for interacting with the Q-Care backend.
- 📱 **Android exploration** — Includes Android-related project files for experimentation with mobile deployment.

## ⚙️ How It Works

Q-Care is organized around a multi-stage information-processing pipeline.

```text
User Input
    |
    v
Safety Checks
    |
    v
Clinical Context Classification
    |
    v
Medical Evidence Retrieval
    |
    v
Evidence Ranking
    |
    v
Evidence Gate
    |
    v
Evidence Adaptation and Fusion
    |
    v
Evidence Confidence Profiling
    |
    v
Experimental QUBO / QAOA Selection
    |
    v
Precautionary Analysis
    |
    v
AI-Assisted Explanation
```

The image workflow adds vision-based observations before relevant information is passed into the assessment pipeline.

## ⚛️ What Does Quantum Computing Do Here?

Q-Care explores **QUBO (Quadratic Unconstrained Binary Optimization)** and **QAOA (Quantum Approximate Optimization Algorithm)** as experimental methods for selecting a relevant subset of retrieved evidence.

The goal is to investigate whether optimization techniques can help balance relevance and selection constraints when working with multiple evidence sources.

**Important:** The quantum component is experimental. The project does not claim quantum advantage, clinical validation, or improved medical outcomes from quantum computing.

## 🧰 Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Conversational AI | Google Gemini API |
| Image analysis | Gemini vision model |
| Medical evidence | WHO, MedlinePlus, CDC integrations |
| Optimization | QUBO / QAOA, Qiskit-based experimentation |
| Data storage | SQLite where applicable |
| Version control | Git and GitHub |
| Mobile exploration | Android project files |

*The availability of individual integrations depends on the configured API keys, network access, and current project implementation.*

## 📂 Project Structure

```text
Q-Care/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── src/
│   │   ├── evidence_engine.py
│   │   ├── gemini_conversation.py
│   │   ├── gemini_vision.py
│   │   └── v2/
│   │       ├── ai_researcher.py
│   │       ├── emergency_engine.py
│   │       ├── evidence_pool.py
│   │       ├── pipeline.py
│   │       ├── quantum_ranker.py
│   │       └── response_engine.py
│   └── tests/
├── frontend/
│   └── index.html
├── android/
├── package.json
├── capacitor.config.json
├── patch_apk.py
└── README.md
```

*The tree highlights major project components; additional files may exist.*

## 🚀 Getting Started

### 1. Prerequisites

Install the following:

- Python 3.11 or another Python version compatible with the project's dependencies
- Git
- A Google Gemini API key for AI functionality
- A working internet connection for external evidence retrieval

### 2. Clone the repository

```bash
git clone https://github.com/Alien-C-Jomon/Q-CARE.git
cd Q-CARE
```

### 3. Create a virtual environment

**Windows Command Prompt:**

```bat
cd backend
python -m venv qcare-env
qcare-env\Scripts\activate
```

### 4. Install dependencies

```bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the location expected by the backend configuration. For example, if the application loads `backend/.env`, create it inside `backend`.

Add your own API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Use the exact environment variable name expected by your configured application. Never commit `.env` files, private keys, or API credentials to GitHub.

### 6. Run Q-Care

From the `backend` directory, run:

```bat
python app.py
```

Open the local address printed by Flask in your browser. If the application is configured to serve the frontend at its root route, that address will open the Q-Care interface.

If startup fails, check the installed dependencies, environment variables, and backend error message.


## 🔐 Gemini API Key Setup

Q-Care uses the **Google Gemini API** for AI-powered conversation and image analysis.

For security, **no API key is included in this repository**. Each user must provide their own Gemini API key locally.

### 1. Get your Gemini API key

Create your own Gemini API key through **Google AI Studio**.

> **Never commit your API key to GitHub or share it publicly.**

### 2. Set the Gemini API key

Q-Care reads the Gemini API key from the **Windows User Environment Variable**:

```text
GEMINI_API_KEY
```

On Windows, open **Command Prompt** and set your own key with:

```cmd
setx GEMINI_API_KEY "YOUR_GEMINI_API_KEY_HERE"
```

Replace `YOUR_GEMINI_API_KEY_HERE` with your own Gemini API key.

### 3. Restart your terminal

After using `setx`, **close the current Command Prompt and open a new one**.

Environment variables created with `setx` are available to newly opened terminals and applications.

### 4. Verify the configuration safely

Do **not** print the API key itself.

Instead, run:

```cmd
if defined GEMINI_API_KEY (echo GEMINI_API_KEY=FOUND) else (echo GEMINI_API_KEY=NOT_FOUND)
```

You should see:

```text
GEMINI_API_KEY=FOUND
```

### 5. Start Q-Care

Start the Q-Care backend normally after configuring the environment variable.

The application reads the key through the environment rather than storing it inside the source code.

### ⚠️ Security Warning

Do **not**:

- Put your API key directly into Python source code.
- Commit an API key to GitHub.
- Add your API key to the README.
- Paste your API key into GitHub Issues, screenshots, or public discussions.
- Share your API key with other people.

If your API key is accidentally exposed, **revoke/rotate it immediately** and create a replacement key.

### 🧪 Important for Contributors

Each installation of Q-Care should use its **own Gemini API key**.

The repository intentionally does not contain a working API key. This prevents credentials from being exposed through version control.

Q-Care's AI components obtain the key from:

```python
os.environ.get("GEMINI_API_KEY")
```

Your API key should remain private to your own local environment.


## 🧪 Testing

From the project root, activate the backend environment and run the available tests:

```bat
cd backend
qcare-env\Scripts\activate
python -m pytest
```

Some tests may require API credentials, network access, or optional dependencies.

## 🔐 Security and Privacy

- Keep API keys in environment variables or a local `.env` file.
- Never commit passwords, private keys, access tokens, or service-account credentials.
- Review `.gitignore` before committing changes.
- Avoid uploading real patient records, identifiable health information, or private medical images.
- Restrict API usage and configure provider-side limits where available.

## 🗺️ Future Development

Potential areas for further development include:

- 🚨 More robust emergency warning and escalation logic.
- 📚 Improved retrieval, source verification, and evidence freshness.
- 🧪 Expanded automated testing and failure handling.
- ⚛️ Better evaluation of quantum-inspired ranking against classical baselines.
- 📱 More reliable Android packaging and deployment.
- 🔒 Stronger privacy controls and security testing.
- 👩‍⚕️ Expert review and formal clinical validation before any real-world healthcare use.

## 🎯 Project Vision

Q-Care explores the intersection of artificial intelligence, medical information retrieval, precautionary health guidance, and quantum optimization.

Its long-term goal is to investigate how these technologies can work together to make relevant health information easier to understand while keeping safety, transparency, and responsible use at the center.

## 👨‍💻 Author

**Joyal C Jomon**

Student developer exploring AI, quantum computing, and real-world problem-solving.

## 📜 License

No license has been specified yet. Unless a license is added to this repository, reuse and redistribution are subject to applicable copyright law.

---

**Built with curiosity, code, and a little quantum ambition. ⚛️💙**
