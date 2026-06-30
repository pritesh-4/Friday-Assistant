import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import {BrowserRouter} from 'react-router-dom'
import {
  ChatProvider,
  SidebarProvider,
  SettingsProvider,
  MemoryProvider
} from "./context";

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <SettingsProvider>
      <SidebarProvider>
        <MemoryProvider>
          <ChatProvider>
            <App />
          </ChatProvider>
        </MemoryProvider>
      </SidebarProvider>
    </SettingsProvider>
  </BrowserRouter>,
)
