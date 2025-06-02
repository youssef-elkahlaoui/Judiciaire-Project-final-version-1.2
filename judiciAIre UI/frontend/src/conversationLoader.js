// This file contains functions to patch into main.tsx
// Add this code to improve conversation loading

// Updated loadConversation function
const loadConversation = useCallback(async (conversationId) => {
  if (!isSignedIn) return Promise.reject(new Error("Not signed in"));
  
  console.log("🔄 Loading conversation:", conversationId);
  
  return new Promise(async (resolve, reject) => {
    try {
      const token = await getToken();
      const response = await fetch(`http://localhost:5000/api/conversations/${conversationId}`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await response.json();
      console.log("📥 Received conversation data:", data);
      
      if (response.ok) {
        // Make sure messages array exists
        if (!data.messages || !Array.isArray(data.messages)) {
          console.error("❌ No messages array in conversation data:", data);
          toast.error("Conversation has no messages");
          reject(new Error("Conversation has no messages"));
          return;
        }
        
        console.log("📋 Original messages format:", data.messages);
        
        // Convert messages from { role, content } format to { sender, text } format expected by App.jsx
        const formattedMessages = data.messages.map(msg => {
          console.log("Processing message:", msg);
          
          // Handle both formats gracefully
          if (msg.role && msg.content !== undefined) {
            return {
              sender: msg.role === "user" ? "user" : "bot",
              text: msg.content
            };
          } else if (msg.sender && msg.text !== undefined) {
            return msg; // Already in the right format
          } else {
            console.warn("⚠️ Message in unexpected format:", msg);
            // Try to salvage what we can
            return {
              sender: msg.role || msg.sender || (msg.user_id ? "user" : "bot"),
              text: msg.content || msg.text || "Message content unavailable"
            };
          }
        });
        
        console.log("🔄 Formatted messages:", formattedMessages);
        
        setMessages(formattedMessages);
        setSelectedConversationId(conversationId);
        resolve(formattedMessages);
      } else {
        console.error("❌ Error loading conversation:", data.error);
        toast.error("Failed to load conversation");
        reject(new Error(data.error || "Failed to load conversation"));
      }
    } catch (error) {
      console.error("❌ Failed to load conversation:", error);
      toast.error("Failed to load conversation");
      reject(error);
    }
  });
}, [isSignedIn, getToken]);
