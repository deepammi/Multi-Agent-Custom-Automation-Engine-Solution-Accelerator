import React, { StrictMode, useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { FluentProvider, teamsLightTheme, teamsDarkTheme } from "@fluentui/react-components";
import { setEnvData, setApiUrl, config as defaultConfig, toBoolean, getUserInfo, setUserInfoGlobal } from './api/config';
import { UserInfo } from './models';
import { apiService } from './api';
const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);

const AppWrapper = () => {
  // State to store the current theme
  const [isConfigLoaded, setIsConfigLoaded] = useState(false);
  const [isUserInfoLoaded, setIsUserInfoLoaded] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
  type ConfigType = typeof defaultConfig;
  const [config, setConfig] = useState<ConfigType>(defaultConfig);
  useEffect(() => {
    const initConfig = async () => {
      // Set default config first
      window.appConfig = defaultConfig;
      setEnvData(defaultConfig);
      setApiUrl(defaultConfig.API_URL);
      
      try {
        // Try to load config from /config.json (static file)
        const response = await fetch('/config.json');
        let loadedConfig = defaultConfig;
        
        if (response.ok) {
          loadedConfig = await response.json();
          loadedConfig.ENABLE_AUTH = toBoolean(loadedConfig.ENABLE_AUTH);
          console.log('✅ Config loaded from /config.json:', loadedConfig);
        } else {
          console.info('ℹ️ Using default config (config.json not found)');
        }

        window.appConfig = loadedConfig;
        setEnvData(loadedConfig);
        setApiUrl(loadedConfig.API_URL);
        setConfig(loadedConfig);
        
        // Handle user info
        let defaultUserInfo = loadedConfig.ENABLE_AUTH ? await getUserInfo() : ({} as UserInfo);
        window.userInfo = defaultUserInfo;
        setUserInfoGlobal(defaultUserInfo);
        
        // Try to send browser language (non-blocking)
        try {
          await apiService.sendUserBrowserLanguage();
        } catch (langError) {
          console.info('ℹ️ Could not send browser language (backend may not be ready)');
        }
      } catch (error) {
        console.error("❌ Error loading config:", error);
        // Use default config on error
        window.appConfig = defaultConfig;
        setEnvData(defaultConfig);
        setApiUrl(defaultConfig.API_URL);
        setConfig(defaultConfig);
      } finally {
        setIsConfigLoaded(true);
        setIsUserInfoLoaded(true);
      }
    };
    
    initConfig(); // Call the async function inside useEffect
  }, []);
  // Effect to listen for changes in the user's preferred color scheme
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleThemeChange = (event: MediaQueryListEvent) => {
      setIsDarkMode(event.matches);
      document.body.classList.toggle("dark-mode", event.matches); // ✅ Add this
    };

    // Apply dark-mode class initially
    document.body.classList.toggle("dark-mode", isDarkMode);

    mediaQuery.addEventListener("change", handleThemeChange);
    return () => mediaQuery.removeEventListener("change", handleThemeChange);
  }, []);
  if (!isConfigLoaded || !isUserInfoLoaded) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        Loading configuration...
      </div>
    );
  }
  
  return (
    <StrictMode>
      <FluentProvider theme={isDarkMode ? teamsDarkTheme : teamsLightTheme} style={{ height: "100vh" }}>
        <App />
      </FluentProvider>
    </StrictMode>
  );
};

// Error Boundary Component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('React Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          padding: '20px', 
          maxWidth: '800px', 
          margin: '50px auto',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
          <h1 style={{ color: '#d32f2f' }}>⚠️ Application Error</h1>
          <p>Something went wrong. Please check the console for details.</p>
          <details style={{ marginTop: '20px' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Error Details</summary>
            <pre style={{ 
              background: '#f5f5f5', 
              padding: '15px', 
              borderRadius: '4px',
              overflow: 'auto',
              marginTop: '10px'
            }}>
              {this.state.error?.toString()}
              {'\n\n'}
              {this.state.error?.stack}
            </pre>
          </details>
          <button 
            onClick={() => window.location.reload()}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              fontSize: '16px',
              cursor: 'pointer',
              background: '#1976d2',
              color: 'white',
              border: 'none',
              borderRadius: '4px'
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Wrap AppWrapper with ErrorBoundary
const AppWithErrorBoundary = () => (
  <ErrorBoundary>
    <AppWrapper />
  </ErrorBoundary>
);
root.render(<AppWithErrorBoundary />);
// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
