import { createRoot } from "react-dom/client";
import { ClerkProvider, useAuth, useClerk, useUser } from "@clerk/clerk-react";
import { BrowserRouter, Routes, Route, useNavigate, Link } from "react-router-dom";
import { SignIn, SignUp } from "@clerk/clerk-react";
import App from "./App.jsx";
import LandingPage from "./components/LandingPage.js";
import { useEffect, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import NotFound from "./components/NotFound.jsx";
import { useCallback } from "react";

// TypeScript declaration for window.authState
declare global {
  interface Window {
    authState: {
      justSignedIn: boolean;
    };
  }
}

const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

// Global flag to handle authentication state
window.authState = {
  justSignedIn: false,
};

// Custom SignIn component
function CustomSignIn() {
  const { isSignedIn } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    console.log("🔁 CustomSignIn useEffect triggered. isSignedIn:", isSignedIn);
    if (isSignedIn) {
      console.log("🎉 CustomSignIn: User is signed in, setting justSignedIn flag");
      try {
        sessionStorage.setItem("justSignedIn", "true");
        window.authState.justSignedIn = true;
        console.log("🔍 justSignedIn set:", {
          sessionStorage: sessionStorage.getItem("justSignedIn"),
          windowAuthState: window.authState.justSignedIn,
        });
      } catch (error) {
        console.error("❌ Error setting sessionStorage:", error);
      }
      navigate("/");
    }
  }, [isSignedIn, navigate]);

  return (
    <div className="flex items-center justify-center h-screen">
      <SignIn afterSignInUrl="/" afterSignUpUrl="/" />
    </div>
  );
}

// Custom SignUp component
function CustomSignUp() {
  const { isSignedIn } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    console.log("🔁 CustomSignUp useEffect triggered. isSignedIn:", isSignedIn);
    if (isSignedIn) {
      console.log("🎉 CustomSignUp: User is signed up, setting justSignedIn flag");
      try {
        sessionStorage.setItem("justSignedIn", "true");
        window.authState.justSignedIn = true;
        console.log("🔍 justSignedIn set:", {
          sessionStorage: sessionStorage.getItem("justSignedIn"),
          windowAuthState: window.authState.justSignedIn,
        });
      } catch (error) {
        console.error("❌ Error setting sessionStorage:", error);
      }
      navigate("/");
    }
  }, [isSignedIn, navigate]);

  return (
    <div className="flex items-center justify-center h-screen">
      <SignUp afterSignInUrl="/" afterSignUpUrl="/" />
    </div>
  );
}

// SignOutButton component
export function SignOutButton() {
  const { signOut } = useClerk();
  const navigate = useNavigate();

  const handleSignOut = () => {
    signOut();
    navigate("/"); // Redirect to landing page after sign out
  };
  return <button onClick={handleSignOut}>Sign Out</button>;
}

// SignOutLink component styled as a navigation link
export function SignOutLink() {
  const { signOut } = useClerk();
  const navigate = useNavigate();

  const handleSignOut = () => {
    signOut();
    navigate("/");
  };
  return <Link to="/sign-out" onClick={handleSignOut}>Sign Out</Link>;
}

// Dedicated SignOut page component
function SignOutPage() {
  const { signOut } = useClerk();
  const navigate = useNavigate();

  useEffect(() => {
    const performSignOut = async () => {
      await signOut();
      navigate("/");
    };

    performSignOut();
  }, [signOut, navigate]);

  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <p className="text-lg mb-4">Signing you out...</p>
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto"></div>
      </div>
    </div>
  );
}

// Root component
function Root() {
  const { isSignedIn, getToken } = useAuth();
  const { user } = useUser();
  const [welcomed, setWelcomed] = useState(false);
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]); // ✅ Add this
  const [selectedConversationId, setSelectedConversationId] = useState(null);

  const generateUniqueId = () => {
    if (window.crypto?.randomUUID) {
      return window.crypto.randomUUID(); // Modern and clean
    } else {
      return "conv_" + Date.now() + "_" + Math.random().toString(36).substring(2, 10); // Fallback
    }
  };

  const fetchConversations = useCallback(async () => {
    try {
      const token = await getToken();
      console.log("🔄 Fetching conversations with token:", token ? "Valid token" : "No token");
      
      const response = await fetch("http://localhost:5000/api/get-convos", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
      });
        const data = await response.json();
      console.log("📥 Received conversation data:", data);
      
      if (response.ok) {
        if (Array.isArray(data)) {
          console.log("✅ Setting conversations array:", data);
          setConversations(data);
        } else if (data.conversations && Array.isArray(data.conversations)) {
          console.log("✅ Setting conversations :", data.conversations);
          setConversations(data.conversations);
        } else {
          console.warn("⚠️ No conversations found in response or unexpected format");
          setConversations([]);
        }
      } else {
        console.error("❌ Error fetching conversations:", data.error);
        toast.error("Failed to load conversations");
      }
    } catch (error) {
      console.error("❌ Failed to fetch conversations:", error.message);
      toast.error("Failed to load conversations");
    }
  }, [getToken,isSignedIn,messages]);

  useEffect(() => {
    if (isSignedIn) {
      console.log("👤 User is signed in, fetching conversations");
      fetchConversations();
    }
  }, [isSignedIn, fetchConversations]);

  // Add function to load a specific conversation
  const loadConversation = useCallback(async (conversationId) => {
    if (!isSignedIn) return;
    
    console.log("🔄 Loading conversation:", conversationId);
    
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
      } else {
        console.error("❌ Error loading conversation:", data.error);
        toast.error("Failed to load conversation");
      }
    } catch (error) {
      console.error("❌ Failed to load conversation:", error);
      toast.error("Failed to load conversation");
    }
  }, [isSignedIn, getToken]);

  useEffect(() => {
    // If there's a selected conversation ID but no messages, load that conversation
    if (isSignedIn && selectedConversationId && messages.length === 0) {
      loadConversation(selectedConversationId);
    }
  }, [isSignedIn, selectedConversationId, messages.length, loadConversation]);

  useEffect(() => {
    const justSignedIn = sessionStorage.getItem("justSignedIn") === "true";
    if (isSignedIn && user) {
      getToken().then((token) => {
        if (!token) {
          console.error("❌ Failed to retrieve token for user save");
          return;
        }
        fetch("http://localhost:5000/api/save-user", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            clerkid: user.id,
            name: user.fullName,
            email: user.emailAddresses[0].emailAddress,
          }),
        })
          .then((response) => {
            if (!response.ok) {
              throw new Error(`Server responded with ${response.status}`);
            }
            return response.json();
          })
          .then((data) => {
            console.log("✅ User saved successfully:", data);
          })
          .catch((err) => {
            console.error("❌ Failed to save user data:", err);
          });
      });
    }

    if (isSignedIn && user && justSignedIn && !welcomed) {
      const userName = user.firstName || user.username || "User";
      toast.success(`👋 Welcome to JudiciAIre, ${userName}!`, {
        duration: 3000,
        position: "top-center",
      });

      setWelcomed(true);
      sessionStorage.setItem("justSignedIn", "false");
    }



    // Save conversation if messages exist
    if (isSignedIn && user && messages.length > 1) {
      (async () => {
        try {          const token = await getToken();
          if (!token) {
            throw new Error("Failed to retrieve token for conversation save");
          }

          const convId = selectedConversationId || generateUniqueId();
          if (!selectedConversationId) setSelectedConversationId(convId);

          // Convert messages from { sender, text } format to { role, content } format expected by backend
          const formattedMessages = messages.map(msg => ({
            role: msg.sender === "user" ? "user" : "assistant",
            content: msg.text
          }));

          const response = await fetch("http://localhost:5000/api/save-convo", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              userId: user?.id,
              title: messages.find(m => m.sender === "user")?.text.slice(0, 20) || "Untitled",
              messages: formattedMessages,
              conversationId: convId,
            }),
          });

          const data = await response.json();
          if (response.ok) {
            console.log("✅ Conversation saved successfully:", data);
            setSelectedConversationId(data.conversationId || convId);
          } else {
            console.error("❌ Error saving conversation:", data.error, data.details);
          }
        } catch (error) {
          console.error("❌ Failed to save conversation:", error.message);
        }
      })();
    }
  }, [isSignedIn, user, welcomed, messages]);



  return (
    <>
      {isSignedIn ? (
        <App
          messages={messages}
          setMessages={setMessages}
          selectedConversationId={selectedConversationId}
          setSelectedConversationId={setSelectedConversationId}
          conversations={conversations}
          loadConversation={loadConversation}
          fetchConversations={fetchConversations}
        />
      ) : (
        <LandingPage />
      )}
      <Toaster position="top-center" reverseOrder={true} />
    </>
  );
}

createRoot(document.getElementById("root")).render(
  <ClerkProvider publishableKey={clerkPubKey}>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Root />} />
        <Route path="/sign-out" element={<SignOutPage />} />
        <Route path="/sign-in" element={<CustomSignIn />} />
        <Route path="/sign-up" element={<CustomSignUp />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  </ClerkProvider>
);