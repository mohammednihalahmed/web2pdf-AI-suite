import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const UploadProgressModal = ({ isVisible }) => {
  if (!isVisible) return null;
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-70 z-50">
      <div className="bg-white px-6 py-4 rounded-lg shadow-md text-center">
        <p className="text-gray-800 font-semibold text-lg mb-2">
          Processing PDF...
        </p>
        <p className="text-sm text-gray-600">
          Please wait while your file is being uploaded and processed.
        </p>
      </div>
    </div>
  );
};

export default function Sidebar({
  user,
  chats,
  setChats,
  setCurrentChat,
}) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [selectedMenuChat, setSelectedMenuChat] = useState(null);
  const [dropdownVisible, setDropdownVisible] = useState(false);
  const [showUploadProgress, setShowUploadProgress] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  const toggleSidebar = () => setSidebarOpen(!isSidebarOpen);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownVisible(false);
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  const handleChatOption = async (chat, option) => {
    const token = localStorage.getItem("token");

    if (option === "rename") {
      const newName = prompt("Enter new chat name:", chat.chat_name);
      if (!newName) return;
      try {
        const res = await fetch(`/chats/${chat.id}?new_name=${newName}`, {
          method: "PUT",
          headers: { Authorization: `Bearer ${token}` },
        });
        const updated = await res.json();
        setChats((prev) =>
          prev.map((c) =>
            c.id === chat.id ? { ...c, chat_name: updated.new_name } : c
          )
        );
      } catch (err) {
        console.error(err);
      }
    } else if (option === "delete") {
      if (!window.confirm(`Delete "${chat.chat_name}"?`)) return;
      try {
        await fetch(`/chats/${chat.id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
        setChats((prev) => prev.filter((c) => c.id !== chat.id));
        setCurrentChat((cur) => (cur?.id === chat.id ? null : cur));
      } catch (err) {
        console.error(err);
      }
    }
    setDropdownVisible(false);
  };

  const handleUploadPdf = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setShowUploadProgress(true);
    const formData = new FormData();
    formData.append("file", file);
    const token = localStorage.getItem("token");

    try {
      const res = await fetch("/upload_pdf/", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        console.error("Upload failed");
        setShowUploadProgress(false);
        return;
      }

      const { filename } = await res.json();
      setShowUploadProgress(false);
      navigate("/chatbot");
    } catch (error) {
      console.error("Upload error:", error);
      setShowUploadProgress(false);
    }
  };

  const handleNewChat = async () => {
    const token = localStorage.getItem("token");
  
    const defaultName = "New Chat";
    try {
      const res = await fetch("/create_chats", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: user.id,
          chat_name: defaultName,
        }),
      });
  
      if (!res.ok) throw new Error("Failed to create chat");
  
      const data = await res.json();
  
      const newChat = {
        id: data.chat_id,
        chat_name: data.chat_name,
        messages: [],
      };
  
      setChats((prev) => [...prev, newChat]);
      setCurrentChat(newChat);
      setSidebarOpen(false);
    } catch (err) {
      console.error("Error creating new chat:", err.message);
    }
  };
  
  

  return (
    <>
      <UploadProgressModal isVisible={showUploadProgress} />

      <button
        className="fixed top-4 left-4 p-2 text-white bg-gray-800 rounded-full shadow-lg z-20"
        onClick={toggleSidebar}
      >
        ☰
      </button>

      <div
        className={`fixed inset-0 bg-gray-800 bg-opacity-60 ${
          isSidebarOpen ? "block" : "hidden"
        }`}
        onClick={toggleSidebar}
      />
      <div
        className={`fixed left-0 top-0 h-full bg-gray-900 text-white w-64 p-6 transition-transform duration-300 z-10 ${
          isSidebarOpen ? "transform-none" : "-translate-x-full"
        }`}
      > 
        <div className="mb-4">
          <button
            onClick={handleNewChat}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            + New Chat
          </button>
        </div>
        <h3 className="text-2xl font-semibold text-gray-200 mb-4">
          Your Chats
        </h3>

        {Array.isArray(chats) && chats.length > 0 ? (
          <ul>
            {chats.map((chat) => (
              <li
                key={chat.id}
                className="relative flex justify-between items-center py-2 px-2 rounded hover:bg-gray-700 cursor-pointer"
                onClick={() => {
                  setCurrentChat(chat);
                  setSidebarOpen(false);
                }}
              >
                <span>{chat.chat_name}</span>
                <div
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedMenuChat(chat);
                    setDropdownVisible((v) =>
                      selectedMenuChat === chat ? !v : true
                    );
                  }}
                  className="px-1"
                >
                  ⋮
                </div>
                {dropdownVisible && selectedMenuChat === chat && (
                  <div
                    ref={dropdownRef}
                    className="absolute right-0 top-full mt-1 bg-white text-gray-900 rounded shadow-lg w-32 z-10"
                  >
                    <div
                      className="px-3 py-1 hover:bg-gray-100 cursor-pointer"
                      onClick={() => handleChatOption(chat, "rename")}
                    >
                      Rename
                    </div>
                    <div
                      className="px-3 py-1 hover:bg-gray-100 cursor-pointer"
                      onClick={() => handleChatOption(chat, "delete")}
                    >
                      Delete
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-400">No chats yet!</p>
        )}

        <div className="mt-6">
          <input
            id="pdf-upload"
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleUploadPdf}
          />
          <label
            htmlFor="pdf-upload"
            className="block w-full text-center py-3 bg-gray-700 rounded hover:bg-gray-600 cursor-pointer"
          >
            Upload PDF
          </label>
        </div>
      </div>
    </>
  );
}
