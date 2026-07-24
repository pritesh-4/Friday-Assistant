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
          <ChatProvider>
            <VoiceProvider>
              <App />
            </VoiceProvider>
          </ChatProvider>
        </MemoryProvider>
      </SidebarProvider>
    </SettingsProvider>
  </BrowserRouter>,
)

