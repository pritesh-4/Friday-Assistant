import { useState, useEffect } from "react";
import { chatService } from "../services/chatService";

/**
 * Custom hook to manage conversation dialogues.
 * @param {string} initialId - Initial active conversation ID.
 */
export function useChat(initialId = null) {
  const [activeConversationId, setActiveConversationId] = useState(initialId);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  // Auto-load conversation messages when activeConversationId changes
  useEffect(() => {
    const loadMessages = async () => {
      if (!activeConversationId) {
        setMessages([]);
        return;
      }
      setIsTyping(true);
      try {
        const history = await chatService.getMessages(activeConversationId);
        // Map backend schema roles to frontend receiver formats if different
        const formatted = history.map((m) => {
          let parsedText = m.content;
          try {
            const data = JSON.parse(m.content);
            if (Array.isArray(data)) {
               // Extract text from structured content
               parsedText = data.map(item => item.text || (item.image_url ? "[Image Attached]" : "")).join(" ").trim();
            }
          } catch {
            // Not JSON
          }
          return {
            sender: m.role,
            text: parsedText,
            time: new Date(m.createdAt).toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
              hour12: false
            }),
            citations: m.citations || [],
            contextAwareness: m.contextAwareness || null,
            emotionalHeader: m.emotionalHeader || null
          };
        });
        setMessages(formatted);
      } catch (err) {
        console.error("Failed to load conversation history:", err);
      } finally {
        setIsTyping(false);
      }
    };
    loadMessages();
  }, [activeConversationId]);

  /**
   * Sends a user message and appends the backend-generated response via streaming.
   * @param {string} text - Message text.
   * @param {Array<string>} fileIds - Array of attached file IDs.
   */
  const sendMessage = async (text, fileIds = []) => {
    if (!text.trim()) return;
    
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;

    // Add user message to state
    const userMsg = { sender: "user", text, time: timeStr };
    
    // Add empty friday message placeholder
    const fridayMsgId = Date.now().toString(); // temporary ID for the stream
    const emptyFridayMsg = {
      id: fridayMsgId,
      sender: "friday",
      text: "",
      time: timeStr,
      isStreaming: true
    };
    
    setMessages((prev) => [...prev, userMsg, emptyFridayMsg]);
    setIsTyping(true);

    try {
      await chatService.streamMessage(
        activeConversationId, 
        text, 
        fileIds, 
        (chunk, metadata, isDone) => {
          if (metadata && metadata.conversationId && !activeConversationId) {
            setActiveConversationId(metadata.conversationId);
          }
          
          if (chunk) {
            setMessages((prev) => {
              const newMsgs = [...prev];
              const lastMsg = newMsgs[newMsgs.length - 1];
              if (lastMsg && lastMsg.id === fridayMsgId) {
                lastMsg.text += chunk;
              }
              return newMsgs;
            });
          }
          
          if (isDone) {
            setIsTyping(false);
            setMessages((prev) => {
              const newMsgs = [...prev];
              const lastMsg = newMsgs[newMsgs.length - 1];
              if (lastMsg && lastMsg.id === fridayMsgId) {
                lastMsg.isStreaming = false;
              }
              return newMsgs;
            });
          }
        }
      );
    } catch (err) {
      console.error("Failed to stream chat message:", err);
      setMessages((prev) => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg && lastMsg.id === fridayMsgId) {
          lastMsg.text = "I could not reach the assistant backend. Please verify that it is running and try again.";
          lastMsg.emotionalHeader = "warning";
          lastMsg.isStreaming = false;
        }
        return newMsgs;
      });
      setIsTyping(false);
    }
  };

  /**
   * Deletes specific message object.
   * @param {string} messageId - Message ID to delete.
   */
  const deleteMessage = (messageId) => {
    setMessages((prev) => prev.filter((m) => m.id !== messageId));
  };

  /**
   * Simulates Friday regenerating the last message.
   */
  const regenerateMessage = () => {
    if (messages.length === 0) return;
    setIsTyping(true);
    setTimeout(() => {
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last && last.sender === "friday") {
          last.text = "New synthesized response stream matrix overlay initialized. Neural pathways recalibrated.";
        }
        return next;
      });
      setIsTyping(false);
    }, 1200);
  };

  return {
    activeConversationId,
    setActiveConversationId,
    messages,
    setMessages,
    sendMessage,
    deleteMessage,
    regenerateMessage,
    isTyping
  };
}
