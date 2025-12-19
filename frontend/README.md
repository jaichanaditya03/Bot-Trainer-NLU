# Bot Trainer Frontend

Modern React + Tailwind CSS frontend for the Bot Trainer NLU application.

## 🚀 Features

- ⚡ **Fast & Responsive**: Built with Vite for lightning-fast HMR
- 🎨 **Modern UI**: Tailwind CSS for beautiful, responsive design
- 🔐 **Authentication**: Complete auth flow with JWT tokens
- 📊 **Dashboard**: Comprehensive workspace and dataset management
- 🎯 **State Management**: Zustand for efficient state handling
- 🔄 **API Integration**: Axios for robust backend communication
- 🎭 **Admin Panel**: User management and system controls

## 📋 Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://127.0.0.1:8000`

## 🛠️ Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file (optional):
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 🏃 Running the Application

### Development Mode
```bash
npm run dev
```
The app will be available at `http://localhost:3000`

### Production Build
```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── auth/          # Authentication components
│   │   ├── common/        # Common UI elements (Card, Loader, etc.)
│   │   └── Sidebar.jsx    # Main navigation sidebar
│   ├── pages/             # Page components
│   │   ├── HomePage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── ForgotPasswordPage.jsx
│   │   ├── DashboardPage.jsx
│   │   └── AdminPanelPage.jsx
│   ├── services/          # API service layers
│   │   ├── api.js         # Axios instance with interceptors
│   │   ├── authService.js
│   │   ├── workspaceService.js
│   │   ├── datasetService.js
│   │   ├── trainingService.js
│   │   └── evaluationService.js
│   ├── store/             # Zustand state management
│   │   ├── authStore.js
│   │   ├── workspaceStore.js
│   │   └── datasetStore.js
│   ├── config/            # Configuration files
│   │   └── config.js
│   ├── App.jsx            # Main app component with routing
│   ├── main.jsx           # Entry point
│   └── index.css          # Global styles with Tailwind
├── public/                # Static assets
├── index.html             # HTML template
├── package.json           # Dependencies and scripts
├── vite.config.js         # Vite configuration
├── tailwind.config.js     # Tailwind CSS configuration
└── postcss.config.js      # PostCSS configuration
```

## 🎯 Key Components

### Authentication
- **Login/Register**: User authentication with JWT tokens
- **Forgot Password**: OTP-based password reset flow
- **Protected Routes**: Route guards for authenticated pages
- **Admin Routes**: Special routes for admin users

### Dashboard
- **Workspace Management**: Create, select, and manage workspaces
- **Dataset Upload**: Upload CSV/JSON training datasets
- **Data Visualization**: View and analyze uploaded data
- **Model Training**: Train NLU models with various algorithms
- **Evaluation**: Test and compare model performance
- **Active Learning**: Intelligent data annotation suggestions

### Admin Panel
- **User Management**: View and manage all users
- **Create Admin**: Add new administrator accounts
- **System Controls**: Configure system settings

## 🔧 Configuration

### API Configuration
Edit `src/config/config.js` to change API base URL:

```javascript
export const API_BASE_URL = 'http://127.0.0.1:8000';
```

### Tailwind Customization
Modify `tailwind.config.js` to customize colors, spacing, etc.

## 🎨 UI Components

### Buttons
```jsx
<button className="btn-primary">Primary Button</button>
<button className="btn-secondary">Secondary Button</button>
<button className="btn-outline">Outline Button</button>
```

### Cards
```jsx
import { Card, CardHeader } from './components/common/Card';

<Card>
  <CardHeader title="Title" subtitle="Subtitle" />
  {/* Content */}
</Card>
```

### Loaders
```jsx
import { Loader, FullPageLoader } from './components/common/Loader';

<Loader size="md" text="Loading..." />
<FullPageLoader text="Please wait..." />
```

## 🔐 State Management

### Auth Store
```javascript
import { useAuthStore } from './store/authStore';

const { token, user, login, logout } = useAuthStore();
```

### Workspace Store
```javascript
import { useWorkspaceStore } from './store/workspaceStore';

const { workspaces, selectedWorkspace, setSelectedWorkspace } = useWorkspaceStore();
```

## 📡 API Services

### Making API Calls
```javascript
import { authService } from './services/authService';

// Login
const response = await authService.login(email, password);

// Register
await authService.register(username, email, password);
```

All API calls automatically include authentication tokens when available.

## 🚨 Error Handling

- API errors are caught and displayed as toast notifications
- 401 responses automatically redirect to login
- Form validation with user-friendly messages

## 🧪 Development Tips

1. **Hot Module Replacement**: Changes reflect instantly during development
2. **React DevTools**: Use browser extension for debugging
3. **Network Tab**: Monitor API calls in browser dev tools
4. **Console Logs**: Check console for error messages

## 📦 Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

## 🤝 Integration with Backend

The frontend expects the following backend endpoints:

- `POST /register` - User registration
- `POST /login` - User login
- `POST /forgot-password` - Request password reset
- `POST /verify-otp` - Verify OTP
- `POST /reset-password` - Reset password
- `GET /workspaces` - Get all workspaces
- `POST /workspaces/create` - Create workspace
- `POST /workspaces/select` - Select workspace
- `POST /datasets` - Upload dataset
- `GET /datasets` - Get all datasets
- `POST /train/start` - Start training
- `GET /train/status` - Get training status
- `GET /admin/users` - Get all users (admin)
- `POST /admin/create-admin` - Create admin user

## 📝 License

This project is part of the Bot Trainer NLU system.

## 👥 Contributing

1. Create a new branch for your feature
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 🐛 Troubleshooting

### Backend Connection Issues
- Ensure backend is running on `http://127.0.0.1:8000`
- Check CORS settings in backend
- Verify API endpoints match

### Build Errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear build cache: `rm -rf dist`
- Check Node.js version: `node --version` (should be 18+)

### Styling Issues
- Rebuild Tailwind: `npm run dev`
- Check tailwind.config.js includes all content paths
- Verify PostCSS is configured correctly

## 📞 Support

For issues or questions, please check the backend API documentation or create an issue in the repository.
