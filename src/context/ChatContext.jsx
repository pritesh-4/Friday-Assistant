/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext } from "react";
import { useChat } from "../hooks/useChat";

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const chat = useChat();

  return (
    <ChatContext.Provider value={chat}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChatContext must be used within a ChatProvider");
  }
  return context;
}
