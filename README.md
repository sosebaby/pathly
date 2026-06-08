# Pathly — AI Immigration Co-Pilot

Pathly is a full-stack AI product that gives personalized immigration 
and travel guidance based on your exact documents and visa status.

Built with FastAPI + Anthropic Claude API.

## Features
- **Trip Checker** — analyzes any route (including transits) and tells 
  you exactly what visas you need, what documents to carry, and flags 
  any restrictions based on your passport and current status
- **PR & Pathway Finder** — surfaces all available permanent residency 
  or citizenship pathways you qualify for, with eligibility requirements, 
  processing times, costs, and official government links

## Stack
- FastAPI (Python backend)
- Anthropic Claude API (claude-sonnet-4-6)
- Pydantic data models
- Plain HTML/CSS/JS frontend

## Setup
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file and add: `ANTHROPIC_API_KEY=your_key_here`
4. Run: `uvicorn main:app --reload`
5. Open `index.html` in your browser

## API Endpoints
- `POST /check-trip` — trip and transit visa checker
- `POST /pathway-finder` — PR and citizenship pathway finder
