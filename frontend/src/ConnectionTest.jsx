import React, { useState } from "react";
import axios from "axios";

const ConnectionTest = () => {
  const [inputText, setInputText] = useState("");
  // const [responseMessage, setResponseMessage] = useState("");
  const [responseData, setResponseData] = useState(null);
  const [rawTextResponse, setRawTextResponse] = useState("");

  const handleSubmit = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:8000/chat", {
        text: inputText,
      });

      let parsed;
      try {
        parsed = JSON.parse(response.data.response); // try to parse JSON

        // If parsed is a plain object — treat it as valid dynamic JSON
        if (parsed && typeof parsed === "object") {
          setResponseData(parsed);
          setRawTextResponse("");
        } else {
          setResponseData(null);
          setRawTextResponse(response.data.response);
        }
      } catch (err) {
        console.log("inside the catch")
        // Fallback for text-based response
        setResponseData(null);
        setRawTextResponse(response.data.response);
      }
    } catch (error) {
      console.error("Error sending data:", error);
    }
  };

  return (
    <div style={{ padding: "1rem", maxWidth: "900px", margin: "auto" }}>
      <h1>Chat with Assistant</h1>

      <input
        type="text"
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        placeholder="Ask anything..."
        style={{ width: "100%", padding: "10px", fontSize: "16px" }}
      />
      <button onClick={handleSubmit} style={{ marginTop: "10px", padding: "10px 20px" }}>
        Send
      </button>

      {/* TEXT Response */}
      {rawTextResponse && (
        <div style={{
          marginTop: "2rem",
          backgroundColor: "#000000",
          padding: "1rem",
          borderRadius: "8px"
        }}>
          <strong>Response:</strong>
          <p>{rawTextResponse}</p>
        </div>
      )}

      {/* GENERIC JSON Response */}
      {responseData && (
        <div style={{
          marginTop: "2rem",
          backgroundColor: "#fefcf2",
          padding: "1rem",
          borderRadius: "12px"
        }}>
          <h3>Structured Response:</h3>
          {Object.entries(responseData).map(([key, value]) => (
            <div
              key={key}
              style={{
                marginBottom: "1rem",
                padding: "0.8rem",
                backgroundColor: "#000000",
                border: "1px solid #ddd",
                borderRadius: "8px"
              }}
            >
              <strong style={{ textTransform: "capitalize" }}>{key.replace(/_/g, " ")}:</strong>
              {Array.isArray(value) ? (
                <ul style={{ marginTop: "0.5rem" }}>
                  {value.map((item, index) => (
                    <li key={index}>{typeof item === "object" ? JSON.stringify(item) : item}</li>
                  ))}
                </ul>
              ) : (
                <p style={{ marginTop: "0.5rem" }}>
                  {typeof value === "object" ? JSON.stringify(value, null, 2) : value}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConnectionTest;


//   return (
//     <div>
//       <h1>Chat with FastAPI</h1>
//       <input
//         type="text"
//         value={inputText}
//         onChange={(e) => setInputText(e.target.value)}
//         placeholder="Enter text here"
//       />
//       <button onClick={handleSubmit}>Send</button>

//       <h2>Response:</h2>
//       <p>{responseMessage}</p>
//     </div>
//   );
// };