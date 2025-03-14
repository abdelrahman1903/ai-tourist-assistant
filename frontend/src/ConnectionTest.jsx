import React, { useState } from "react";
import axios from "axios";

const ConnectionTest = () => {
  const [inputText, setInputText] = useState("");
  const [responseMessage, setResponseMessage] = useState("");

  const handleSubmit = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:8000/chat", {
        text: inputText,  // ✅ Send text as JSON body
      });

      setResponseMessage(response.data.response); // ✅ Use correct response field
    } catch (error) {
      console.error("Error sending data:", error);
    }
  };

  return (
    <div>
      <h1>Chat with FastAPI</h1>
      <input
        type="text"
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        placeholder="Enter text here"
      />
      <button onClick={handleSubmit}>Send</button>

      <h2>Response:</h2>
      <p>{responseMessage}</p>
    </div>
  );
};

export default ConnectionTest;
