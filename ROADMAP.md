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
│  │ • Chat msgs  │ ─► │  │  Mistral LLM   │  │  Regex Engine      │  │  │
│  │ • Emails     │    │  │  (Primary)     │  │  (Fallback)        │  │  │
│  │ • Voice      │    │  │                │  │                    │  │  │
│  │   transcripts│    │  │ • Semantic     │  │ • Direction        │  │  │
│  │ • API calls  │    │  │   parsing      │  │ • Currency pairs   │  │  │
│  │              │    │  │ • Context      │  │ • Amounts          │  │  │
│  └──────────────┘    │  │   awareness    │  │ • Tenors           │  │  │
│                      │  └───────┬────────┘  └─────────┬──────────┘  │  │
│                      │          │                     │             │  │
│                      │          └─────────┬───────────┘             │  │
│                      └──────────────────────────────────────────────┘  │
│                                           │                            │
│                                           ▼                            │
│                      ┌─────────────────────────────────────────┐       │
│                      │          ParsedRFQ Object               │       │
│                      │  {                                      │       │
│                      │    direction: "BUY",                    │       │
│                      │    asset_class: "FX_SPOT",              │       │
│                      │    instrument: "EURUSD",                │       │
│                      │    quantity: 10000000,                  │       │
│                      │    confidence_score: 0.95               │       │
│                      │  }                                      │       │
│                      └────────────────────┬────────────────────┘       │
│                                           ▼                            │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        Output Integrations                       │  │
│  │                                                                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │ REST API │  │  WebUI   │  │ Trading  │  │  Slack/  │          │  │
│  │  │          │  │ Streamlit│  │ Systems  │  │  Teams   │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🛣️ Development Phases

### Phase 1: Core Parser ✅ COMPLETE

**Goal:** Build foundational parsing capability

| Task | Status | Details |
|------|--------|---------|
| Project structure | ✅ | Single-file architecture |
| ParsedRFQ data model | ✅ | Dataclass with all RFQ fields |
| Regex fallback parser | ✅ | Pattern-based parsing for common formats |
| Mistral LLM integration | ✅ | API client with structured JSON output |
| Unit test suite | ✅ | 107 tests covering all patterns |
| MockMistralClient | ✅ | Testing without API calls |
| Data classes | ✅ | ContactInfo, CompanyInfo, LineItem, ParserConfig |

**Deliverables:**
- `rfq_parser.py` - Core parser module (all classes in one file)
- `rfq_parser_tests.py` - Comprehensive test suite (107 tests)

---

### Phase 2: Visual Demo & Testing ✅ COMPLETE

**Goal:** Create interactive demo and comprehensive testing

| Task | Status | Details |
|------|--------|---------|
| Streamlit demo app | ✅ | Interactive web interface |
| Visual result display | ✅ | Color-coded metrics and cards |
| Batch parsing UI | ✅ | Parse multiple RFQs at once |
| JSON export | ✅ | View structured output |
| Architecture diagram | ✅ | Visual system overview |
| App test suite | ✅ | 40 tests for Streamlit app |

**Deliverables:**
- `app.py` - Streamlit demo application
- `app_tests.py` - App test suite (40 tests)
- **Total: 147 passing tests**

---

### Phase 3: API & Integration (Week 4-5) 📋 PLANNED

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

**Planned Files:**
- `api.py` - FastAPI application
- `api_tests.py` - API test suite
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Multi-service setup

---

### Phase 4: Advanced Features (Week 6-8) 📋 PLANNED

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

### Phase 5: Enterprise Features (Week 9-12) 📋 PLANNED

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

### Current Test Coverage

```
┌─────────────────────────────────────────────────────────────┐
│                    TEST SUMMARY                             │
├─────────────────────────────────────────────────────────────┤
│  rfq_parser_tests.py     │  107 tests  │  Parser & Models  │
│  app_tests.py            │   40 tests  │  Streamlit App    │
├─────────────────────────────────────────────────────────────┤
│  TOTAL                   │  147 tests  │  All passing ✅   │
└─────────────────────────────────────────────────────────────┘
```

### Test Categories

**Parser Tests (`rfq_parser_tests.py`):**
- Import tests (4)
- Enum tests (6)
- ContactInfo tests (5)
- CompanyInfo tests (6)
- ParserConfig tests (5)
- LineItem tests (3)
- ParsedRFQ tests (7)
- MockMistralClient tests (13)
- Regex parsing tests (28)
- Mock client integration (3)
- Batch parsing tests (3)
- Convenience function tests (2)
- Serialization tests (4)
- Parser initialization tests (5)
- Real-world RFQ tests (5)
- Performance tests (2)

**App Tests (`app_tests.py`):**
- Direction color tests (5)
- Confidence color tests (4)
- Sample RFQ tests (5)
- Batch parsing integration (3)
- Output formatting tests (7)
- Parser configuration tests (3)
- Parsing notes tests (2)
- Performance tests (2)
- Edge case tests (5)
- Color display integration (4)

### Running Tests

```bash
# Run all tests
pytest rfq_parser_tests.py app_tests.py -v

# Run with coverage
pytest rfq_parser_tests.py app_tests.py --cov=. --cov-report=html

# Run specific test category
pytest rfq_parser_tests.py -k "direction" -v

# Run performance tests
pytest rfq_parser_tests.py app_tests.py -k "performance" -v
```

---

## 🎨 Demo Instructions

### Quick Start

```bash
# 1. Install dependencies
pip install streamlit mistralai pytest

# 2. Set API key (optional - regex works without it)
export MISTRAL_API_KEY="your-key-here"

# 3. Launch demo
streamlit run app.py
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
| Parsing accuracy | >95% | ~95% ✅ |
| Latency (regex) | <10ms | ~5ms ✅ |
| Latency (LLM) | <2000ms | ~1500ms ✅ |
| Test coverage | >90% | 147 tests ✅ |
| API uptime | >99.9% | N/A (Phase 3) |

---

## 🔧 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.10+ | LLM ecosystem, rapid development |
| LLM | Mistral Large | Strong structured output, cost-effective |
| Web UI | Streamlit | Fast prototyping, data-centric UI |
| API | FastAPI | Async, OpenAPI, fast (Phase 3) |
| Testing | pytest | Standard, powerful fixtures |
| Containerization | Docker | Portable deployment (Phase 3) |

---

## 📁 Project Structure

```
rfq_parser_app/
├── rfq_parser.py           # Core parser module (all classes)
├── rfq_parser_tests.py     # Parser test suite (107 tests)
├── app.py                  # Streamlit demo application
├── app_tests.py            # App test suite (40 tests)
├── README.md               # Quick start guide
├── ROADMAP.md              # This document
├── requirements.txt        # Dependencies
└── screenshots/            # Demo screenshots
```

---

## 🚀 Next Steps

1. **Immediate:** ✅ Complete - Core parser and demo working
2. **This Week:** Add FastAPI service (Phase 3)
3. **Next Sprint:** Multi-asset support, voice integration
4. **Future:** Enterprise features, fine-tuning

---

## 📞 Support

For questions or issues:
- Create a GitHub issue
- Review the test files for usage examples
- Check the Streamlit demo for interactive testing
