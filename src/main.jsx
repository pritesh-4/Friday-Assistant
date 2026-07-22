import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import {BrowserRouter} from 'react-router-dom'
import {
  ChatProvider,
  SidebarProvider,
  SettingsProvider,
  MemoryProvider,
  VoiceProvider
} from "./context";

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <SettingsProvider>
      <SidebarProvider>
        <MemoryProvider>
          <VoiceProvider>
            <ChatProvider>
              <App />
            </ChatProvider>
          </VoiceProvider>
        </MemoryProvider>
      </SidebarProvider>
    </SettingsProvider>
  </BrowserRouter>,
)
