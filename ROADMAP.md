# RFQ Parser - Development Roadmap

## 📋 Project Overview

An intelligent Request for Quote (RFQ) parser that converts free-form trading messages into structured data using Mistral LLM with regex fallback.

**Target Users:** Trading desks, sales teams, operations, and automated trading systems

**Key Value Proposition:** Reduce manual data entry, improve quote turnaround time, and enable systematic analysis of RFQ flow.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          RFQ PARSER SYSTEM                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐    ┌──────────────────────────────────────────────┐  │
│  │   Inputs     │    │              Processing Layer                │  │
│  │              │    │  ┌────────────────┐  ┌────────────────────┐  │  │
│  │ • Chat msgs  │───▶│  │  Mistral LLM   │  │  Regex Engine      │  │  │
│  │ • Emails     │    │  │  (Primary)     │  │  (Fallback)        │  │  │
│  │ • Voice      │    │  │                │  │                    │  │  │
│  │   transcripts│    │  │ • Semantic     │  │ • Direction        │  │  │
│  │ • API calls  │    │  │   parsing      │  │ • Currency pairs   │  │  │
│  │              │    │  │ • Context      │  │ • Amounts          │  │  │
│  └──────────────┘    │  │   awareness    │  │ • Tenors           │  │  │
│                      │  └───────┬────────┘  └─────────┬──────────┘  │  │
│                      │          │                     │             │  │
│                      │          └──────────┬──────────┘             │  │
│                      └──────────────────────────────────────────────┘  │
│                                           │                            │
│                      ┌────────────────────▼────────────────────┐       │
│                      │          ParsedRFQ Object               │       │
│                      │                                         │       │
│                      │  {                                      │       │
│                      │    direction: "BUY",                    │       │
│                      │    asset_class: "FX_SPOT",              │       │
│                      │    instrument: "EURUSD",                │       │
│                      │    quantity: 10000000,                  │       │
│                      │    confidence_score: 0.95               │       │
│                      │  }                                      │       │
│                      └────────────────────┬────────────────────┘       │
│                                           │                            │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                        Output Integrations                        │ │
│  │                                                                    │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │ │
│  │  │ REST API │  │  WebUI   │  │ Trading  │  │  Slack/  │          │ │
│  │  │          │  │(Streamlit)│ │ Systems  │  │  Teams   │          │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🛣️ Development Phases

### Phase 1: Core Parser (Week 1-2) ✅

**Goal:** Build foundational parsing capability

| Task | Status | Details |
|------|--------|---------|
| Project structure | ✅ | Python package with src/tests/demo |
| ParsedRFQ data model | ✅ | Dataclass with all RFQ fields |
| Regex fallback parser | ✅ | Pattern-based parsing for common formats |
| Mistral LLM integration | ✅ | API client with structured JSON output |
| Unit test suite | ✅ | pytest tests covering all patterns |
| Basic CLI interface | ✅ | Command-line parsing capability |

**Deliverables:**
- `rfq_parser.py` - Core parser module
- `test_rfq_parser.py` - Comprehensive test suite
- Working regex + LLM parsing

---

### Phase 2: Visual Demo & Testing (Week 3) ✅

**Goal:** Create interactive demo and comprehensive testing

| Task | Status | Details |
|------|--------|---------|
| Streamlit demo app | ✅ | Interactive web interface |
| Visual result display | ✅ | Color-coded metrics and cards |
| Batch parsing UI | ✅ | Parse multiple RFQs at once |
| JSON export | ✅ | Download parsed results |
| Architecture diagram | ✅ | Visual system overview |

**Deliverables:**
- `demo/app.py` - Streamlit application
- Interactive parsing interface
- Batch processing capability

---

### Phase 3: API & Integration (Week 4-5) 🔄

**Goal:** Production-ready API service

| Task | Status | Details |
|------|--------|---------|
| FastAPI service | 📋 Planned | REST endpoints for parsing |
| Authentication | 📋 Planned | API key management |
| Rate limiting | 📋 Planned | Request throttling |
| Async processing | 📋 Planned | Handle concurrent requests |
| OpenAPI docs | 📋 Planned | Auto-generated API documentation |
| Docker container | 📋 Planned | Containerized deployment |

**Planned Endpoints:**
```
POST /parse          - Parse single RFQ
POST /parse/batch    - Parse multiple RFQs
GET  /health         - Health check
GET  /docs           - OpenAPI documentation
```

---

### Phase 4: Advanced Features (Week 6-8) 📋

**Goal:** Enhanced parsing and analytics

| Task | Status | Details |
|------|--------|---------|
| Multi-asset support | 📋 Planned | Bonds, IRS, CDS, Commodities |
| Voice-to-RFQ | 📋 Planned | Whisper integration |
| Entity extraction | 📋 Planned | Client names, counterparties |
| Historical analytics | 📋 Planned | RFQ trend analysis |
| Model fine-tuning | 📋 Planned | Train on proprietary RFQ data |
| Confidence calibration | 📋 Planned | Improve scoring accuracy |

---

### Phase 5: Enterprise Features (Week 9-12) 📋

**Goal:** Production deployment and monitoring

| Task | Status | Details |
|------|--------|---------|
| Observability | 📋 Planned | Logging, metrics, tracing |
| A/B testing | 📋 Planned | Compare LLM vs regex accuracy |
| Feedback loop | 📋 Planned | Human-in-loop corrections |
| Audit trail | 📋 Planned | Compliance logging |
| Multi-tenant | 📋 Planned | Client isolation |
| SLA monitoring | 📋 Planned | Latency and uptime tracking |

---

## 🧪 Testing Strategy

### Test Pyramid

```
                    ┌─────────────────┐
                    │    E2E Tests    │  ← Manual + Automated
                    │   (10% effort)  │
                    ├─────────────────┤
                    │ Integration     │  ← API + LLM tests
                    │ Tests (20%)     │
                    ├─────────────────┤
                    │   Unit Tests    │  ← Parser logic
                    │   (70% effort)  │
                    └─────────────────┘
```

### Test Categories

1. **Unit Tests** (`tests/test_rfq_parser.py`)
   - Direction parsing (BUY/SELL/TWO_WAY)
   - Amount extraction (MM, K, B notation)
   - Currency pair detection
   - Tenor recognition
   - Urgency classification
   - Edge cases (empty, malformed)

2. **Integration Tests**
   - LLM API connectivity
   - Fallback mechanism
   - Batch processing
   - JSON serialization

3. **Performance Tests**
   - Latency benchmarks
   - Throughput testing
   - Memory profiling

4. **Accuracy Tests**
   - Golden dataset validation
   - Confidence score calibration
   - False positive/negative rates

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test category
pytest tests/ -k "direction" -v

# Run performance tests
pytest tests/ -k "performance" -v
```

---

## 🎨 Demo Instructions

### Quick Start

```bash
# 1. Install dependencies
pip install streamlit mistralai

# 2. Set API key (optional - regex works without it)
export MISTRAL_API_KEY="your-key-here"

# 3. Launch demo
streamlit run demo/app.py
```

### Demo Features

| Feature | Description |
|---------|-------------|
| **Single Parse** | Parse one RFQ with detailed output |
| **Sample RFQs** | Pre-loaded examples for testing |
| **Visual Metrics** | Color-coded direction, confidence |
| **JSON Export** | View structured output |
| **Batch Mode** | Parse multiple RFQs in table view |
| **Architecture View** | System diagram in expandable panel |

### Demo Walkthrough

1. **Basic Parsing**
   - Enter: `Buy 10MM EUR/USD spot`
   - Click "Parse RFQ"
   - See: Direction=BUY, Asset=FX_SPOT, Quantity=10M

2. **Complex RFQ**
   - Enter: `URGENT: Need two-way on 50 MIO GBPUSD 3M forward`
   - See: Direction=TWO_WAY, Tenor=3M, Urgency=IMMEDIATE

3. **Batch Processing**
   - Expand "Batch Parsing"
   - Enter multiple RFQs, one per line
   - View results in data table

---

## 📊 Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Parsing accuracy | >95% | TBD |
| Latency (regex) | <10ms | ~5ms |
| Latency (LLM) | <2000ms | ~1500ms |
| Test coverage | >90% | ~85% |
| API uptime | >99.9% | N/A |

---

## 🔧 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.10+ | LLM ecosystem, rapid development |
| LLM | Mistral Large | Strong structured output, cost-effective |
| Web UI | Streamlit | Fast prototyping, data-centric UI |
| API | FastAPI | Async, OpenAPI, fast |
| Testing | pytest | Standard, powerful fixtures |
| Containerization | Docker | Portable deployment |

---

## 📁 Project Structure

```
rfq_parser/
├── src/
│   ├── __init__.py
│   └── rfq_parser.py      # Core parser module
├── tests/
│   └── test_rfq_parser.py # Test suite
├── demo/
│   └── app.py             # Streamlit demo
├── docs/
│   └── ROADMAP.md         # This document
├── requirements.txt       # Dependencies
├── README.md             # Quick start guide
└── setup.py              # Package setup
```

---

## 🚀 Next Steps

1. **Immediate:** Run tests, try the demo
2. **This Week:** Add FastAPI service
3. **Next Sprint:** Multi-asset support, voice integration
4. **Future:** Enterprise features, fine-tuning

---

## 📞 Support

For questions or issues:
- Create a GitHub issue
- Review the test cases for usage examples
- Check the Streamlit demo for interactive testing
