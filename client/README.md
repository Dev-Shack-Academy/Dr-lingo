# Frontend - React + TypeScript

React frontend for the Medical Translation Chat System.

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client with JWT handling
- **React Router** - Routing

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

Development server runs at `http://localhost:5173`

## Project Structure

```
client/
├── src/
│   ├── api/                    # API layer
│   │   ├── HttpClient.ts      # Axios with JWT interceptors
│   │   ├── routes.ts          # API route constants
│   │   └── services/          # API service classes
│   │       ├── AuthService.ts
│   │       ├── ChatService.ts
│   │       └── CollectionService.ts
│   │
│   ├── components/             # React components
│   │   ├── auth/              # Authentication
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   ├── UserMenu.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   │
│   │   ├── admin/             # Admin panel
│   │   │   ├── KnowledgeBaseManagement.tsx
│   │   │   └── PatientContextManagement.tsx
│   │   │
│   │   ├── ChatRoomList.tsx
│   │   ├── TranslationChat.tsx
│   │   ├── MessageBubble.tsx
│   │   └── PatientContextManager.tsx
│   │
│   ├── contexts/               # React contexts
│   │   └── AuthContext.tsx    # Authentication state
│   │
│   ├── pages/                  # Page components
│   │   ├── AuthPage.tsx
│   │   └── TranslationChatPage.tsx
│   │
│   ├── App.tsx                # Main app with routing
│   └── main.tsx               # Entry point
│
├── public/                     # Static assets
├── index.html                 # HTML template
├── vite.config.js             # Vite configuration
├── tailwind.config.js         # Tailwind configuration
└── tsconfig.json              # TypeScript configuration
```

## Features

### Authentication
- JWT-based authentication
- Automatic token refresh on 401 responses
- Protected routes for authenticated users
- Role-based UI (Patient, Doctor, Admin)

### Chat
- Real-time message polling (3-second interval)
- Voice recording and transcription
- Toggle between original and translated text
- Audio playback for voice messages

### Admin Panel
- User management (CRUD)
- Knowledge Base management
- Patient Context management with KB linking
- Chat room management

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

## Commands

```bash
# Development
npm run dev

# Build
npm run build

# Lint
npm run lint

# Format
npm run format

# Type check
npm run typecheck
```

## API Integration

The frontend uses Axios with automatic JWT handling:

```typescript
// HttpClient automatically adds Authorization header
import { httpClient } from './api/HttpClient';

// All requests include JWT token
const response = await httpClient.get('/api/chat-rooms/');
```

### Token Refresh

When a 401 response is received, the client automatically:
1. Attempts to refresh the token
2. Retries the original request
3. Redirects to login if refresh fails

## User Roles

| Role | Access |
|------|--------|
| Patient | Chat, view own messages |
| Doctor | Chat, patient context, AI assistance |
| Admin | Full access, user management, collections |

## Styling

Uses Tailwind CSS with a black and white theme:

```jsx
// Example component styling
<div className="bg-white border border-gray-200 rounded-lg p-4">
  <h2 className="text-gray-900 font-semibold">Title</h2>
  <p className="text-gray-600">Content</p>
</div>
```

## Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [TypeScript](https://www.typescriptlang.org/)
