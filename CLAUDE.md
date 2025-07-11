# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an intelligent Mahjong assistance tool (@����w) that provides real-time game analysis and optimal play suggestions. The project uses a modern full-stack architecture with React frontend and FastAPI backend.

## Development Commands

### Backend (Python FastAPI)
```bash
# Start backend server
cd backend
python start_server.py

# Install dependencies
cd backend
pip install -r requirements.txt

# Run backend directly
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React TypeScript)
```bash
# Start frontend development server
cd frontend
npm start

# Install dependencies
cd frontend
npm install

# Build for production
cd frontend
npm run build

# Run tests
cd frontend
npm test
```

### Prerequisites
- Redis server must be running (required for backend)
- Node.js 18+ for frontend
- Python 3.11+ for backend

## Architecture

### Frontend Stack
- **React 18** with TypeScript for type safety
- **Tailwind CSS** for styling with atomic classes
- **Zustand** for lightweight state management
- **Framer Motion** for animations
- **Axios** for API communication

### Backend Stack
- **FastAPI** with Python 3.11+ for high-performance APIs
- **Redis** for caching and session management
- **WebSocket** support for real-time communication
- **Pydantic** for data validation and serialization

### Key Directories
```
frontend/src/
   components/     # React components (MahjongTable, GameBoard, etc.)
   hooks/         # Custom hooks (useWebSocket, useSettings)
   stores/        # Zustand state stores
   types/         # TypeScript type definitions
   utils/         # Utility functions

backend/app/
   api/           # API routes and endpoints
   models/        # Pydantic data models
   services/      # Business logic services
   algorithms/    # Mahjong game logic and analysis
   websocket/     # WebSocket connection handling
```

## Core Features

1. **Real-time Mahjong Analysis** - AI-powered optimal play suggestions
2. **Remaining Cards Calculator** - Track cards left in play
3. **Win Probability Analysis** - Calculate winning chances
4. **WebSocket Integration** - Real-time game state synchronization
5. **Replay System** - Game replay and analysis functionality

## Development Guidelines

### Frontend Patterns
- Use functional components with TypeScript interfaces
- Implement proper error boundaries for game errors
- Use Tailwind CSS atomic classes for styling
- Follow React Query patterns for API state management
- Implement WebSocket hooks for real-time updates

### Backend Patterns
- Use FastAPI with Pydantic models for data validation
- Implement async/await patterns for all I/O operations
- Use Redis for caching game states and analysis results
- Follow RESTful API design with proper HTTP status codes
- Implement WebSocket endpoints for real-time communication

### Mahjong Logic
- Card representation: numeric IDs for different suits (wan, tiao, tong)
- Game state management through Redis for persistence
- Algorithm implementations for win detection and probability calculation
- Support for standard Mahjong rules with missing suit constraints

## API Endpoints

- `POST /api/mahjong/analyze` - Analyze current game state
- `GET /api/v1/replay/{replay_id}` - Get replay data
- `WebSocket /api/ws` - Real-time game communication

## Important Notes

- The project includes both Chinese and English documentation
- WebSocket connections require proper error handling and reconnection logic
- Redis must be running before starting the backend server
- The frontend expects the backend to be running on port 8000
- Game analysis uses Monte Carlo simulations for probability calculations