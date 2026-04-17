# AI Diary Companion - Frontend

React + Vite + TypeScript frontend for the AI Diary Companion application.

## Features

- User authentication (login/register)
- Chat interface with AI companion
- Diary list view
- JWT token management
- Responsive design following Apple design system
- Protected routes with automatic redirect

## Setup

1. Install dependencies:

```bash
npm install
```

2. Configure environment variables:

```bash
cp .env.example .env
```

Edit `.env` to set your backend API URL (default: `http://localhost:8000`)

3. Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Project Structure

```
src/
├── api/            # API client and HTTP configuration
├── components/     # Reusable React components
├── pages/          # Page components (Login, Register, Chat, Diaries)
├── types/          # TypeScript type definitions
├── hooks/          # Custom React hooks (future)
├── App.tsx         # Main app component with routing
└── main.tsx        # Application entry point
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Tech Stack

- **React 19.x** - UI library
- **Vite 6.x** - Build tool and dev server
- **TypeScript** - Type safety
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **ESLint + Prettier** - Code quality and formatting

## Authentication Flow

1. User logs in or registers
2. JWT token is stored in localStorage
3. Token is automatically added to all API requests via axios interceptor
4. On 401 error, user is redirected to login page
5. Protected routes check for token before allowing access

## Design System

The UI follows an Apple-inspired design system with:

- SF Pro Display/Text typography
- Binary color scheme (black/light gray sections)
- Apple Blue accent color for interactive elements
- Responsive breakpoints for mobile, tablet, and desktop
- Accessibility-compliant focus states

See `DESIGN.md` in the project root for complete design specifications.

## API Integration

The frontend connects to the backend API at the URL specified in `VITE_API_BASE_URL`.

### Endpoints Used:

- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user
- `POST /characters/1/chat` - Send chat messages
- `GET /diaries` - List user diaries
- `GET /diaries/:id` - Get specific diary
- `POST /diaries` - Create new diary
- `PUT /diaries/:id` - Update diary
- `DELETE /diaries/:id` - Delete diary

## Development Notes

- The app uses React 19's new features
- State management is handled with React hooks (useState, useEffect)
- No global state library is used yet (could add Redux/Zustand if needed)
- API client is a singleton instance with interceptors for auth
