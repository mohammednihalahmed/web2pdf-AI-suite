// src/components/Conversation.js
import React from "react";

export default function Conversation({ messages }) {
  return (
    <div className="flex-grow overflow-y-auto p-4 space-y-3 flex flex-col">
      {messages.map((msg, i) => (
        <div
          key={i}
          className={`max-w-xl p-3 rounded-lg shadow self-${
            msg.sender === "user" ? "end bg-blue-100" : "start bg-white"
          }`}
        >
          <div className="text-sm text-gray-500 mb-1">
            {new Date(msg.timestamp).toLocaleString()}
          </div>
          <div className="whitespace-pre-wrap">{msg.message}</div>
        </div>
      ))}
    </div>
  );
}
