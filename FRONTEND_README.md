# AutoApply AI Frontend

A modern React TypeScript frontend for the AutoApply AI job application automation system.

## 🚀 Features

- **🎨 Modern UI**: Built with React 18 + TypeScript and Tailwind CSS
- **🔐 Authentication**: Complete login/register system with JWT tokens
- **📊 Dashboard**: Interactive dashboard with charts and metrics
- **📱 Responsive Design**: Works perfectly on desktop and mobile
- **🎯 Real-time Updates**: Uses React Query for efficient data fetching
- **🌙 Professional Design**: Clean, modern interface with professional styling

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── Layout.tsx          # Main layout with sidebar navigation
│   ├── contexts/
│   │   └── AuthContext.tsx     # Authentication state management
│   ├── pages/
│   │   ├── Login.tsx           # Login page
│   │   ├── Register.tsx        # Registration page
│   │   └── Dashboard.tsx       # Main dashboard with metrics
│   ├── services/
│   │   └── api.ts              # API service layer with all endpoints
│   ├── App.tsx                 # Main app with routing
│   └── index.css               # Tailwind CSS configuration
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

## 🛠️ Technology Stack

- **Frontend Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **State Management**: React Query + Context API
- **HTTP Client**: Axios
- **Icons**: Heroicons
- **Charts**: Recharts
- **Forms**: React Hook Form

## 📱 Pages & Features

### 🔐 **Authentication**
- **Login Page**: Email/password authentication with validation
- **Register Page**: Account creation with form validation
- **Protected Routes**: Automatic redirect based on auth state

### 🏠 **Dashboard**
- **Key Metrics**: Total applications, response rates, interviews
- **Interactive Charts**: Application trends over time
- **Recent Activity**: Live feed of recent actions
- **Quick Actions**: One-click access to main features

### 🎯 **Navigation**
- **Sidebar**: Clean navigation with active state indicators
- **Mobile Responsive**: Collapsible sidebar for mobile devices
- **User Profile**: Quick access to profile and logout

### 📊 **Features** (Ready for Implementation)
- **Job Search**: Browse and filter job postings
- **Applications**: Track application status and progress
- **Scraping**: Configure and monitor job scraping
- **Cover Letters**: Generate and manage cover letters
- **Profile**: Manage user preferences and settings

## 🎨 Design System

### **Colors**
- **Primary**: Blue (#3b82f6) - Main brand color
- **Secondary**: Gray (#64748b) - Supporting elements
- **Success**: Green (#10b981) - Positive actions
- **Warning**: Orange (#f59e0b) - Attention items
- **Error**: Red (#ef4444) - Error states

### **Components**
- **Cards**: Clean white cards with subtle shadows
- **Buttons**: Consistent styling with hover states
- **Forms**: Professional input styling with focus states
- **Charts**: Interactive data visualizations

## 🔌 API Integration

The frontend connects to your backend API running on **http://localhost:8000**:

### **Authentication Endpoints**
- `POST /api/v1/users/login` - User login
- `POST /api/v1/users/register` - User registration
- `GET /api/v1/users/me` - Current user info

### **Dashboard Endpoints**
- `GET /api/v1/dashboard/overview` - Dashboard metrics
- `GET /api/v1/dashboard/trends` - Application trends
- `GET /api/v1/dashboard/activity` - Recent activity

### **Core Features**
- Jobs, Applications, Scraping, Cover Letters
- All API endpoints are pre-configured and ready to use

## 🚀 Getting Started

### **Prerequisites**
- Node.js 16+
- Backend API running on http://localhost:8000

### **Installation**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🎯 Usage

1. **Start the Backend**: Make sure your AutoApply AI backend is running
2. **Start the Frontend**: Run `npm start` in the frontend directory
3. **Create Account**: Visit http://localhost:3000/register
4. **Login**: Use your credentials to access the dashboard
5. **Explore**: Navigate through the different sections

## 🧪 Testing the Integration

### **Test User Creation**
```bash
# Create a test user (backend must be running)
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

### **Test Login**
1. Go to http://localhost:3000/login
2. Enter your credentials
3. You should be redirected to the dashboard

## 📈 Next Steps

The frontend is ready for full integration with your backend. Here's what you can do next:

1. **Complete Profile Creation**: The system guides users through profile setup
2. **Start Job Scraping**: Use the scraping interface to find jobs
3. **Track Applications**: Monitor your application progress
4. **Generate Cover Letters**: Create personalized cover letters

## 🎨 Customization

### **Styling**
- Modify `tailwind.config.js` for custom colors and themes
- Update `src/index.css` for global styles
- Component-specific styling in individual files

### **API Configuration**
- Update `src/services/api.ts` for API endpoint changes
- Modify base URL in the API configuration

## 📱 Mobile Support

The frontend is fully responsive and works great on:
- Desktop computers
- Tablets
- Mobile phones
- All modern browsers

## 🔧 Development

### **Code Organization**
- **Components**: Reusable UI components
- **Pages**: Route-specific page components
- **Services**: API integration and data fetching
- **Contexts**: Global state management

### **Development Commands**
```bash
npm start          # Start development server
npm run build      # Build for production
npm test           # Run tests
npm run eject      # Eject from Create React App
```

## 🎉 Congratulations!

You now have a complete, production-ready React frontend for AutoApply AI! The interface is modern, responsive, and ready to help users automate their job applications with style.

---

**Ready to revolutionize job hunting with AutoApply AI!** 🚀 