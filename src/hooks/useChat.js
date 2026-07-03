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
        const formatted = history.map((m) => ({
          sender: m.role,
          text: m.content,
          time: new Date(m.createdAt).toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false
          }),
          citations: m.citations || [],
          contextAwareness: m.contextAwareness || null,
          emotionalHeader: m.emotionalHeader || null
        }));
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
   * Sends user message prompt and triggers simulated response.
   * @param {string} text - Message text.
   */
  const sendMessage = async (text) => {
    if (!text.trim()) return;
    
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;

    // Add user message to state
    const userMsg = { sender: "user", text, time: timeStr };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    // Call service layer for storage persistence
    const result = await chatService.sendMessage(activeConversationId, text);
    const targetConversationId = result.conversationId;

    // Simulate Friday typing response
    setTimeout(async () => {
      const responseTemplates = [
        {
          text: "### Telemetry diagnostics complete.\n- Connection matrix: **Aligned**\n- Compilation speed: **380ms**\n\nI have created a config wrapper:\n```javascript\nconst fridayConfig = {\n  identity: \"F.R.I.D.A.Y.\",\n  syncRate: 0.998,\n  status: \"active\"\n};\n```\nLet's run compile scripts when you are ready, Boss.",
          emotionalHeader: "ideas",
          citations: [{ label: "1. Diagnostic Sheet", url: "#" }]
        },
        {
          text: "### Database logs synced.\n> \"The question is less about intelligence and more about how we choose to use it.\"\n\nI have adjusted the workspace variables for your project. Ready to continue.",
          contextAwareness: "interests",
          emotionalHeader: "discovered"
        },
        {
          text: "### Synthesizer diagnostics online.\n- Voice telemetry: **Calibrated**\n- Neural pathways: **Stabilized**\n\nI'm ready to receive audio inputs.",
          emotionalHeader: "interesting"
        }
      ];

      const selected = responseTemplates[Math.floor(Math.random() * responseTemplates.length)];
      
      const fridayMsg = await chatService.saveResponse(targetConversationId, selected);
      
      const formatted = {
        sender: "friday",
        text: fridayMsg.content,
        time: new Date(fridayMsg.createdAt).toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false
        }),
        citations: fridayMsg.citations || [],
        contextAwareness: fridayMsg.contextAwareness || null,
        emotionalHeader: fridayMsg.emotionalHeader || null
      };

      setMessages((prev) => [...prev, formatted]);
      setIsTyping(false);
      
      // If a new conversation was created, trigger setting it active
      if (result.isNew) {
        setActiveConversationId(targetConversationId);
      }
    }, 1500);
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
