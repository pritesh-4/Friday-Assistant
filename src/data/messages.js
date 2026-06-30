export const mockMessages = {
  "chat-1": [
    {
      id: "msg-101",
      conversationId: "chat-1",
      role: "friday",
      content: "Good evening, Boss. The system interfaces are fully synced and the memory cores are online. How would you like to proceed?",
      createdAt: "2026-06-30T19:58:00Z",
      status: "completed"
    }
  ],
  "chat-2": [
    {
      id: "msg-201",
      conversationId: "chat-2",
      role: "user",
      content: "Let's brainstorm a new AI startup idea.",
      createdAt: "2026-06-30T18:28:00Z",
      status: "completed"
    },
    {
      id: "msg-202",
      conversationId: "chat-2",
      role: "friday",
      content: "### Startup Concept: NeuralNotes\n- Description: **Context-aware knowledge base** that synthesizes voice notes automatically.\n- Stack: Next.js + Vector Storage\n\nHere is a simple structure:\n```javascript\nconst startup = {\n  name: 'NeuralNotes',\n  growthRate: 1.2,\n  isActive: true\n};\n```\nWhat do you think, Boss?",
      createdAt: "2026-06-30T18:30:00Z",
      status: "completed"
    }
  ],
  "chat-3": [
    {
      id: "msg-301",
      conversationId: "chat-3",
      role: "user",
      content: "How does backpropagation work in deep learning?",
      createdAt: "2026-06-29T14:18:00Z",
      status: "completed"
    },
    {
      id: "msg-302",
      conversationId: "chat-3",
      role: "friday",
      content: "### Backpropagation Basics\nBackpropagation computes gradients of loss functions with respect to network weights:\n\n> Gradient descent updates weights in the opposite direction of the gradient.\n\n- Step 1: Forward pass to compute output.\n- Step 2: Calculate error loss function.\n- Step 3: Backward pass using chain rule gradients.",
      createdAt: "2026-06-29T14:20:00Z",
      status: "completed"
    }
  ]
};
