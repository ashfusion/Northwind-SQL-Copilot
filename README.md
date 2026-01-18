# Text-to-SQL Pipeline

A **Text-to-SQL engine** built using **LangChain** and **Ollama**.

The system uses a **dual-model architecture**:

- 🧑‍💻 **Coder model** → Responsible for generating SQL queries
- ✍️ **Writer model** → Converts raw database results into clear, human-readable answers

> _One model writes SQL. Another explains it like a sane human._

---

## ✨ Key Features

### 🔀 Dual-Model Architecture

- **SQL Generation Model**: `qwen3-coder`
- **Natural Language Response Model**: `smollm2`
- Fully configurable via environment variables

### 📜 Logging

- Structured **JSON logging**
- Logs stored by date: `logs/YYYY-MM-DD.log`
- Captures:

  - Full prompts sent to each model
  - Model names used
  - Generated SQL
  - Raw database output
  - Execution time per pipeline step

### 🧠 Prompt Strategy Support

- Multiple prompt sizes supported:

  - `short` → Recommended for medium to large models
  - `tiny` → Optimized for small models

- Helps prevent prompt overflow and hallucinations

### 🧼 Input & Output Sanitization

- Cleans malformed SQL before execution
- Sanitizes database output before passing to the NLP model
- Reduces hallucinations from lightweight models

---

## 📁 Project Structure

```
.
├── main.py                  # CLI entry point
├── src/
│   ├── pipeline.py          # Core Text-to-SQL pipeline logic
│   ├── config.py            # Prompts, constants, and settings
│   ├── models.py            # Pydantic data models
│   └── logger_utils.py      # Logging configuration
└── logs/                    # Auto-generated execution logs
```

---

## ⚙️ Setup

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 2️⃣ Environment Configuration

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=user
DB_PASS=password
DB_SCHEMA=text_to_sql

SQL_MODEL=qwen3-coder:30b
NLP_MODEL=smollm2:latest
NLP_MODEL_TYPE=short   # Options: short | tiny
```

> **Tip:** Use `tiny` only for low-resource environments. Expect reduced answer quality.

---

## ▶️ Running the Project

### Run with Default Question

```bash
python main.py
```

### Run with a Custom Question

```bash
python main.py "How many customers are there?"
```

---

## 🪵 Logging Details

All execution logs are stored in the `logs/` directory.

Each run records:

- Timestamp
- SQL model name
- NLP model name
- Full prompts sent to both models
- Generated SQL
- Raw database results
- Execution time for every pipeline step

---
