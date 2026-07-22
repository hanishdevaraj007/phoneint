# PhoneINT 🔍
> Phone Number OSINT Intelligence Tool

A Python-based OSINT utility that performs carrier lookup, number validation, geolocation profiling, and surface-level intelligence analysis on a target phone number using open-source data sources — no paid API keys required (for the core feature set).

PhoneINT is evolving from a single CLI script into a modular OSINT framework with a plugin-based core engine, a CLI, and a web-based GUI dashboard — all sharing the same intelligence engine.

---

## ⚠️ Disclaimer

> This tool is intended for **educational purposes and authorized OSINT investigations only**.
> Misuse of this tool to target individuals without consent may violate laws in your jurisdiction (stalking, harassment, and privacy statutes in most countries).
> The author is not responsible for any misuse. Do not use PhoneINT against a number without a lawful basis or the subject's consent.

---

## Status

**Current version:** CLI-only, single-file script (`phoneINT.py`)
**In progress:** Core engine refactor → plugin architecture → CLI/GUI split (see [Roadmap](#roadmap--architecture) below)

---

## ✅ Current Features (v1 — CLI)

- **Validation & normalization** — E164, International, and National formats via `phonenumbers`
- **Carrier & line-type identification** — Mobile, Fixed Line, VoIP, Toll Free, Premium Rate, MVNO hints
- **Country-level geolocation** — capital, region, subregion, coordinates, population, Google Maps link (via `restcountries.com`, no key required)
- **Timezone resolution** — all timezones associated with the number's region
- **OSINT surface analysis** — flags anomalies: VoIP usage, unresolved carrier (possible MVNO/eSIM/porting), unresolved region (possible satellite/non-geographic number)
- **JSON report export** — `--export` flag saves a timestamped intelligence report
- **Interactive & argument modes** — run with a number as an argument or be prompted
- **Color-coded terminal report** — readable, structured CLI output

### Requirements
```
phonenumbers
requests
```

### Usage
```bash
python phoneINT.py                      # interactive mode
python phoneINT.py +919876543210        # direct lookup
python phoneINT.py +919876543210 --export   # save JSON report
```

---

## 🧭 Roadmap & Architecture

The project is moving from a single script to a **three-layer architecture**: a reusable core engine, and two interfaces (CLI + GUI) that both call it.

```
phoneint/
├── phoneint_core/           # Core engine — pure logic, no I/O side effects
│   ├── engine.py            # Orchestrates plugin execution & result aggregation
│   ├── models.py            # Structured dataclasses for results (NumberProfile, etc.)
│   ├── correlation.py       # Cross-references results across plugins, scores confidence
│   ├── scoring.py           # Composite risk/trust score calculation
│   └── plugins/             # One file per intelligence module (see below)
│       ├── base.py          # Plugin interface: run(number) -> dict
│       ├── validation.py    # (current) phonenumbers-based validation
│       ├── geolocation.py   # (current) restcountries-based geolocation
│       ├── breach_check.py  # HaveIBeenPwned-linked lookups
│       ├── reputation.py    # Fraud/spam reputation scoring (Numverify/AbstractAPI/IPQS)
│       ├── footprint.py     # Generates reverse-lookup & social search URLs
│       └── porting.py       # Number porting / carrier-history detection
│
├── cli/
│   └── phoneint_cli.py       # Thin CLI wrapper over phoneint_core
│
├── gui/
│   ├── app.py                 # FastAPI/Flask backend, calls phoneint_core
│   └── frontend/               # Web dashboard (case view, batch upload, reports)
│
├── reports/
│   ├── json_exporter.py
│   ├── pdf_exporter.py         # New: polished case-report PDF
│   └── graph_exporter.py       # New: node/edge export (Maltego/Gephi compatible)
│
├── audit/
│   └── logger.py               # Investigation purpose + audit trail logging
│
├── tests/
├── requirements.txt
└── README.md
```

### Planned Feature Tiers

**Tier 1 — Deepen existing capability**
- [ ] Line-type confidence scoring instead of a flat category
- [ ] Number porting / carrier-history detection
- [ ] Batch mode — CSV input, bulk report output

**Tier 2 — New enrichment sources**
- [ ] Breach exposure check (HaveIBeenPwned API)
- [ ] Fraud/reputation scoring (Numverify, AbstractAPI, or IPQualityScore)
- [ ] Footprint URL generation — reverse-lookup and social search links (Google, Telegram, WhatsApp click-to-chat, etc.) without scraping private/authenticated data
- [ ] Username correlation pivot (WhatsMyName-style, when a name/handle surfaces)

**Tier 3 — Differentiators**
- [ ] **Correlation engine** — cross-references results across plugins into a single confidence-scored profile, not just a list of raw hits
- [ ] **Composite trust/risk score** — transparent, explainable scoring (not a black box)
- [ ] **Plugin architecture** — third parties can add a module by implementing one interface; auto-discovered and run by the engine
- [ ] **Case management** — save, tag, and revisit investigations over time
- [ ] **Export formats** — PDF case report, CSV, and graph export (Maltego/Gephi-compatible node/edge format)
- [ ] **Consent/audit gating** — mandatory investigation-purpose field and audit log before a lookup runs

### Interfaces

- **CLI** — current script, refactored to call `phoneint_core` instead of containing logic directly
- **GUI (web dashboard)** — local FastAPI/Flask backend + frontend for case management, batch upload, and visual reports; runs on the same engine as the CLI

---

## Comparison Context

Existing tools in this space (PhoneInfoga, Blackbird, SpiderFoot, Maltego, and paid all-in-one platforms) tend to win on **breadth of correlated sources and usable reporting**, not any single lookup. PhoneINT's differentiation plan is:
1. Batch processing + cross-source correlation (most free tools skip this)
2. A genuinely modular, documented plugin system (invites contribution, like SpiderFoot)
3. Built-in consent/audit gating as a first-class feature, not an afterthought

---

## Installation

```bash
git clone https://github.com/yourusername/phoneint.git
cd phoneint
pip install -r requirements.txt
```

---

## Contributing

Once the plugin architecture lands, contributions will follow this pattern:
1. Create a new file under `phoneint_core/plugins/`
2. Implement the `run(number: PhoneNumber) -> dict` interface from `plugins/base.py`
3. The engine auto-discovers and runs it — no core code changes required

(Contribution guide will be expanded once Tier 1 refactor is complete.)

---

## Future Scaling
- Full web-application deployment alongside the CLI tool
- Plugin marketplace / community-contributed modules
- Integration with other OSINT tooling via graph export (Maltego, Gephi)

---

## Author

**Hanish D** — Cybersecurity Researcher | [GitHub](https://github.com/hanishdevaraj007) | [LinkedIn](https://linkedin.com/in/hanishd)