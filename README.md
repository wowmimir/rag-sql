

### **Phase 1 — Core Intelligence**

* Schema filtering (table-level selection)
* Column-level retrieval (schema compression)
* SQL generation refinement (structured output, SELECT-only)

---

### **Phase 2 — Agent Engine (LangGraph)**

* LangGraph orchestration (state machine design)
* Nodes: generate → validate → execute → repair
* Self-correcting loop (retry on errors, bounded iterations)

---

### **Phase 3 — Backend System**

* FastAPI backend (`/query`, `/schema`, `/health`)
* CSV upload → DB ingestion pipeline
* Dynamic schema updates from uploaded data

---

### **Phase 4 — Frontend**

* React / Next.js / Streamlit UI
* CSV upload interface
* Chat-based query system
* Display: SQL + result + final answer

---

### **Phase 5 — Deployment**

* Dockerization (backend + DB + optional vector store)
* Cloud deployment (Render / Railway / Fly.io / AWS)

---

## 🔁 System Flow

Schema → Column retrieval → SQL generation → Validation → Execution → Self-repair (LangGraph loop) → Natural language answer → UI
