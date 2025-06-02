// Debug helper for conversation data
// Add this to your browser console to help debug the conversation loading issue

window.debugConversation = (conversationId) => {
  const token = localStorage.getItem('clerk-db-jwt'); // Attempt to get token from localStorage
  
  if (!token) {
    console.error('No authentication token found. Please make sure you are logged in.');
    return;
  }
  
  console.log(`🔍 Debugging conversation: ${conversationId}`);
  
  fetch(`http://localhost:5000/api/conversations/${conversationId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    console.log(`Status: ${response.status}`);
    return response.json();
  })
  .then(data => {
    console.log('Conversation data:', data);
    
    if (data.messages && Array.isArray(data.messages)) {
      console.log(`Messages (${data.messages.length}):`);
      data.messages.forEach((msg, index) => {
        console.log(`Message ${index}:`, msg);
        
        // Check format inconsistencies
        if (msg.role && !msg.sender) {
          console.log(`- Using 'role' format: ${msg.role}/${msg.content}`);
        } else if (msg.sender && !msg.role) {
          console.log(`- Using 'sender' format: ${msg.sender}/${msg.text}`);
        } else {
          console.log(`- Unusual format:`, msg);
        }
      });
    } else {
      console.error('No messages array found in the conversation data');
    }
  })
  .catch(error => {
    console.error('Error fetching conversation:', error);
  });
};

// Usage: Run in browser console
// debugConversation('your-conversation-id');
