import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Conversation from "../components/Conversation";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { AiOutlineArrowUp } from "react-icons/ai";
import { useRef } from "react";
import { useNavigate } from 'react-router-dom'; 

const Chatbot = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [chats, setChats] = useState([]);
  const [currentChat, setCurrentChat] = useState(null);
  const [messages, setMessages] = useState([]);

  const messagesEndRef = useRef(null);


  const [userInput, setUserInput] = useState("");
  const [pdfMode, setPdfMode] = useState(false);
  const [pdfList, setPdfList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedPdf, setSelectedPdf] = useState({
    id: null,
    filename: null,
    chunk_filename: null,
  });
 
    // ➊ Load chats once
    useEffect(() => {
      async function loadChats() {
        const { data } = await axios.get("/chats", {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        setChats(data);
      }
      loadChats();
    }, [user.token]);

    // ➋ Whenever currentChat changes, fetch its messages
  useEffect(() => {
      if (!currentChat) {
        setMessages([]);
        return;
      }
      async function loadHistory() {
        const { data } = await axios.get(
          `/chats/${currentChat.id}/messages`,
          { headers: { Authorization: `Bearer ${user.token}` } }
        );
        setMessages(data.messages);
      }
      loadHistory();
    }, [currentChat, user.token]);

  // Fetch PDFs each time PDF mode is enabled
  useEffect(() => {
    const fetchUserPdfs = async () => {
      if (!pdfMode) return;
      try {
        const { data } = await axios.get("/pdfs", {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        setPdfList(data.pdfs || []);
      } catch (error) {
        console.error("fetch PDFs error:", error.response?.data || error.message);
        setPdfList([]);
      }
    };
    fetchUserPdfs();
  }, [pdfMode, user.token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  

  const handlePdfSelect = async (e) => {
    const fileId = e.target.value;
    if (!fileId) return;
    try {
      const { data } = await axios.post(`/select_pdf?file_id=${fileId}`, null, {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      const selected = pdfList.find((f) => f.id === parseInt(fileId));
      setSelectedPdf({
        id: selected.id,
        filename: selected.filename,
        chunk_filename: data.chunk_filename,
      });
    } catch (e) {
      console.error("selectPDF error:", e.response?.data || e.message);
      setSelectedPdf({ id: null, filename: null, chunk_filename: null });
    }
  };


  // 4️⃣ Send message & receive bot reply
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    setLoading(true);

    let chatId = currentChat?.id;
    // ➊ If no chat yet, create one
    if (!chatId) {
      try {
        const { data: chatData } = await axios.post(
          "/create_chats",
          {
            user_id: user.id,
            chat_name: userInput,         // use first query as chat name
          },
          {
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${user.token}`,
            },
          }
        );
        // build new chat object
        const newChat = {
          id: chatData.chat_id,
          chat_name: chatData.chat_name,
          messages: [],
        };
        setChats((prev) => [...prev, newChat]);
        setCurrentChat(newChat);
        chatId = chatData.chat_id;
      } catch (err) {
        console.error("Create chat error:", err.response?.data || err.message);
        setLoading(false);
        return;
      }
    }

    // ➋ Now send the user’s message to /chat
    const payload = {
      query: userInput,
      mode: pdfMode ? "pdf" : "general",
      chat_id: chatId,
      chunk_filename: selectedPdf?.chunk_filename || null,
    };
    console.log("▶️ Sending to /chat:", payload);

    try {
      const { data } = await axios.post("/chat", payload, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${user.token}`,
        },
      });

      // Append messages to the current chat
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === chatId
            ? {
                ...chat,
                messages: [
                  ...chat.messages,
                  { sender: "user", message: userInput, timestamp: new Date().toISOString() },
                  { sender: "bot", message: data.response, timestamp: new Date().toISOString() },
                ],
              }
            : chat
        )
      );
      // Also update currentChat to trigger re-render
      setCurrentChat((prev) =>
        prev?.id === chatId
          ? {
              ...prev,
              messages: [
                ...prev.messages,
                { sender: "user", message: userInput, timestamp: new Date().toISOString() },
                { sender: "bot", message: data.response, timestamp: new Date().toISOString() },
              ],
            }
          : prev
      );
      setUserInput("");
    } catch (err) {
      console.error("Message send error:", err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="flex flex-col h-screen">
      <Sidebar
        user={user}
        chats={chats}
        setChats={setChats}
        setCurrentChat={setCurrentChat}
      />

      <div className="flex flex-grow flex-col bg-gray-50">
        <div className="sticky top-0 z-0 flex justify-between items-center p-4 border-b bg-white">
          <h1 className="text-xl font-semibold">Chatbot</h1>
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={pdfMode}
                onChange={() => {
                  setPdfMode(!pdfMode);
                  setSelectedPdf({ id: null, filename: null, chunk_filename: null });
                }}
                className="form-checkbox"
              />
              <span>PDF Mode</span>
            </label>

            {pdfMode && (
              <select
                value={selectedPdf.id || ""}
                onChange={handlePdfSelect}
                className="border rounded px-2 py-1"
              >
                <option value="" disabled>
                  {pdfList.length === 0 ? "No PDFs found" : "Select PDF..."}
                </option>
                {pdfList.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.filename}
                  </option>
                ))}
              </select>
            )}

            <button className="bg-red-600 text-white px-3 py-1 rounded" onClick={
                ()=> {
                  logout();
                  navigate('/login');
                }
              } 
            >
              Logout
            </button>
          </div>
        </div>

          {/* ➍ Render our new Conversation component */}
          <>
          <Conversation messages={messages} />
          <div ref={messagesEndRef} />
          </>

        <form
          onSubmit={handleSendMessage}
          className="sticky bottom-0 z-10 flex items-center p-4 bg-white border-t space-x-2"
        >
          <textarea
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            rows={1}
            placeholder="Ask something..."
            className="flex-grow resize-none px-4 py-2 border rounded focus:outline-none focus:ring"
            disabled={loading}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white p-3 rounded-full hover:bg-blue-700 disabled:opacity-50"
          >
            <AiOutlineArrowUp size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chatbot;

