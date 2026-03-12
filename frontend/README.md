# Frontend - Compliance & Transaction Management System

A modern Next.js-based web application for compliance monitoring, transaction management, and user administration built with React 19 and TypeScript.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: v18.0 or higher 
- **npm** or **pnpm**: Package managers for Node.js
  - npm comes with Node.js
  - pnpm (recommended): `npm install -g pnpm`

## Quick Start

### 1. Install Dependencies

Using **pnpm** (recommended):
```bash
cd frontend
pnpm install
```

Or using **npm**:
```bash
cd frontend
npm install
```

### 2. Run Development Server

Start the development server:

```bash
pnpm dev
# or
npm run dev
```

The application will be available at:
- **Local**: http://localhost:3000
- **Network**: http:/\/your-ip:3000

### 3. Build for Production

Create an optimized production build:

```bash
pnpm build
```

### 4. Start Production Server

Run the production build:

```bash
pnpm start
# or
npm start
```

## Project Structure

```
src/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Home page
│   ├── globals.css              # Global styles
│   └── main/                    # Main application routes
│       ├── layout.tsx
│       ├── page.tsx
│       ├── add-user/            # User creation
│       ├── admin-management/    # Admin controls
│       ├── cns/                 # CNS (Compliance Notification System)
│       ├── compliance/          # Compliance monitoring
│       ├── dashboard/           # Main dashboard
│       ├── help/                # Help & documentation
│       ├── legacy/              # Legacy features
│       ├── settings/            # User settings
│       ├── superadmin/          # Super admin panel
│       ├── transactions/        # Transaction management
│       └── users/               # User management
├── components/                  # Reusable React components
│   ├── AlertClassificationCard.tsx
│   ├── ApiDiagnostics.tsx
│   ├── HealthCheckWrapper.tsx
│   ├── HealthStatusCard.tsx
│   ├── MetricCard.tsx
│   ├── ServerDown.tsx
│   ├── StatusBadge.tsx
│   ├── SystemAlertCard.tsx
│   └── ui/                      # UI primitives (Radix UI)
│       ├── avatar.tsx
│       ├── badge.tsx
│       ├── button.tsx
│       ├── card.tsx
│       ├── dropdown-menu.tsx
│       ├── input.tsx
│       ├── select.tsx
│       └── table.tsx
├── data/                        # Static data & constants
│   └── users.ts
├── hooks/                       # Custom React hooks
│   ├── useApi.ts               # API communication hook
│   └── useHealthCheck.ts       # Health check hook
└── lib/                         # Utility libraries
    ├── api.ts                  # API client configuration
    ├── transformers.ts         # Data transformation utilities
    └── utils.ts                # General utilities
```

## Available Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start development server with hot reload |
| `pnpm build` | Create production build |
| `pnpm start` | Run production server |
| `pnpm lint` | Run ESLint to check code quality |
| `pnpm lint:fix` | Fix linting issues automatically |

## Technology Stack

- **Framework**: [Next.js 16](https://nextjs.org/) - React framework with SSR/SSG
- **React**: v19.2.0 - UI library
- **TypeScript**: v5 - Type safety
- **Styling**: 
[Tailwind CSS 4](https://tailwindcss.com/) - Utility-first CSS
- **UI Components**: [Radix UI](https://www.radix-ui.com/) - Accessible component library
- **Icons**: [Lucide React](https://lucide.dev/) - Icon library
- **Utilities**:
  - `clsx` - Class composition utility
  - `tailwind-merge` - Merge Tailwind CSS classes
  - `class-variance-authority` - Type-safe component variants
- **Dev Tools**:
  - **ESLint** v9 - Code linting
  - **TypeScript** - Type checking

## API Integration

The frontend connects to a backend API. Configuration is typically done in:

- `src/lib/api.ts` - API client setup
- `src/hooks/useApi.ts` - API communication hook

Ensure the backend API is running before starting the frontend. Update the API base URL in the configuration files if needed.

## Configuration

### Environment Variables

Create a `.env.local` file in the `frontend/` directory if you need environment-specific configuration:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### Next.js Configuration

Modify `next.config.ts` to customize build behavior, redirects, rewrites, etc.

### TypeScript Configuration

Check `tsconfig.json` for TypeScript compiler options.

## Code Quality

### Run Linter

```bash
pnpm lint
```

### Fix Linting Issues

```bash
pnpm lint:fix
```

## Troubleshooting

### Port Already in Use

If port 3000 is already in use:

```bash
pnpm dev -- -p 3001
# or
npm run dev -- -p 3001
```

### Dependencies Issues

Clear cache and reinstall:

```bash
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

Or with npm:

```bash
rm -rf node_modules package-lock.json
npm install
```

### Build Errors

Ensure all TypeScript errors are resolved:

```bash
pnpm build
```

Check for any type errors in the console output.

## Features

- **Dashboard**: System overview with key metrics
- **User Management**: Add, edit, and manage users
- **Transaction Monitoring**: View and analyze transactions
- **Compliance Tracking**: Monitor compliance status
- **Admin Panel**: Administrative controls for system management
- **Health Monitoring**: System health and diagnostic checks
- **Notifications**: Real-time alerts and notifications
- **Settings**: User and system configuration

