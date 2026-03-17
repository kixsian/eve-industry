# EVE Online Manufacturing Calculator

Phase 1 MVP: Recursive material breakdown with cost analysis for EVE Online manufacturing.

## Setup

### Prerequisites
- Docker & docker-compose
- Python 3.11+ (for SDE download script)
- Node.js 20+ (for frontend dependencies)

### Quick Start

1. **Clone and enter the project**
   ```bash
   cd ~/projects/eve-industry-calc
   ```

2. **Download the SDE (one-time setup)**
   ```bash
   cd backend
   pip install -r requirements.txt
   python scripts/download_sde.py
   cd ..
   ```

3. **Start services with docker-compose**
   ```bash
   docker-compose up
   ```

   This will start:
   - PostgreSQL on `:5432`
   - Backend API on `:8000`
   - Frontend on `:3000`

4. **Visit the app**
   Open http://localhost:3000

## Phase 1 Features

### Calculate Manufacturing Costs
1. Search for a blueprint (e.g., "Rifter")
2. Configure:
   - Number of runs
   - Material Efficiency level (0-10)
   - Structure bonus (EC = 0.01)
   - Rig bonus (T1 = 0.02)
   - Whether to break down T2/composite materials
3. View:
   - Recursive material tree
   - Shopping list (flat materials)
   - Cost summary with Jita prices
   - Profit margins and markup calculator

### API Endpoints

**Calculate Manufacturing**
```
POST /api/manufacturing/calculate
{
  "product_type_id": 17736,
  "runs": 10,
  "me_level": 10,
  "structure_bonus": 0.01,
  "rig_bonus": 0.02,
  "build_intermediates": true
}
```

**Search Items**
```
GET /api/manufacturing/search?q=Rifter&limit=50
```

## Architecture

- **Backend**: FastAPI + SQLAlchemy + httpx
- **Frontend**: React + TypeScript + Vite
- **Database**: PostgreSQL (app cache) + SQLite (SDE read-only)
- **Market Data**: Fuzzwork Market API (30-min cache)

## Material Adjustment Formula

```
quantity = base × ((100 - ME) / 100) × (1 - structure_bonus) × (1 - rig_bonus) × runs
result = max(runs, ceil(round(quantity, 2)))
```

Where:
- ME = Material Efficiency (0-10)
- structure_bonus = EC = 0.01 (1%)
- rig_bonus = T1 Rig = 0.02 (2%) in highsec

## Roadmap

- **Phase 2**: EVE SSO authentication + multi-character support
- **Phase 3**: Asset integration (personal + corp hangars)
- **Phase 4**: Structure config, job management, character assignment
- **Phase 5**: Polish (shopping list export, markup config, background sync)

## Notes

- Phase 1 MVP does not require EVE Online account/API keys
- All prices pulled from Jita via Fuzzwork API
- SDE data is read-only SQLite from Fuzzwork
