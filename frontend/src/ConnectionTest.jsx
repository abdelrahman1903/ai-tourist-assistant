import React, { useState, useRef } from "react";
import axios from "axios";
import { FaMicrophone, FaStop, FaPaperPlane, FaUpload } from "react-icons/fa";

const ConnectionTest = () => {
  const [inputText, setInputText] = useState("");
  // const [responseMessage, setResponseMessage] = useState("");
  // const [responseData, setResponseData] = useState(null);
  // const [rawTextResponse, setRawTextResponse] = useState("");
  const [messages, setMessages] = useState([]); // Holds all messages (both user and assistant)
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "http://localhost:8000/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      console.log("Upload successful:", response.data);
    } catch (error) {
      console.error("Upload error:", error);
    }
  };

  const handleSubmit = async () => {
    if (!inputText.trim()) return;

    const userMessage = { type: "user", text: inputText };
    setMessages((prev) => [...prev, userMessage]);
    setInputText(""); // Clear input
    try {
      const response = await axios.post("http://127.0.0.1:8000/chat", {
        text: inputText,
      });

      let parsed;
      let assistantMessage;
      try {
        parsed = JSON.parse(response.data.response); // try to parse JSON
        assistantMessage = {
          type: "assistant",
          text: parsed,
          isJson: true,
        };
        // If parsed is a plain object — treat it as valid dynamic JSON
        // if (parsed && typeof parsed === "object") {
        //   setResponseData(parsed);
        //   setRawTextResponse("");
        // } else {
        //   setResponseData(null);
        //   setRawTextResponse(response.data.response);
        // }
      } catch (err) {
        assistantMessage = {
          type: "assistant",
          text: response.data.response,
          isJson: false,
        };
        // Fallback for text-based response
        // setResponseData(null);
        // setRawTextResponse(response.data.response);
      }
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending data:", error);
    }
  };

  const handleStartRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); //Asks the user to allow access to the microphone, Returns an audio stream

    mediaRecorderRef.current = new MediaRecorder(stream);
    chunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (event) => {
      //Every time the browser has some recorded audio ready, this callback runs
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    mediaRecorderRef.current.onstop = () => {
      //Combines all chunks into a single audio file
      const blob = new Blob(chunksRef.current, { type: "audio/wav" });
      uploadAudio(blob);
    };

    mediaRecorderRef.current.start();
    setIsRecording(true);
  };

  const handleStopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const uploadAudio = async (blob) => {
    //send audio to the server
    const formData = new FormData();
    formData.append("audio", blob, "recording.wav");
    console.log(blob.type); // from React
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/audio",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      //   const data = await response.json();
      // console.log("Transcription:", response.data.Transcription);
      setInputText(response.data.Transcription);
    } catch (error) {
      console.error("Error uploading audio:", error);
    }
  };

  return (
    <div
      style={{
        padding: "2rem",
        maxWidth: "800px",
        margin: "auto",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h1>Chat with Assistant</h1>

      {/* TEXT Response */}
      <div style={{ marginTop: "1rem" }}>
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              marginBottom: "10px",
              padding: "10px",
              borderRadius: "10px",
              backgroundColor: msg.type === "user" ? "#010101" : "#111111",
              alignSelf: msg.type === "user" ? "flex-end" : "flex-start",
            }}
          >
            {msg.isJson ? (
              <div
                style={{
                  backgroundColor: "#1e1e1e",
                  borderRadius: "10px",
                  padding: "10px",
                  color: "#ffffff",
                }}
              >
                {Object.entries(msg.text).map(([key, value], idx) => (
                  <div
                    key={idx}
                    style={{
                      backgroundColor: "#2a2a2a",
                      padding: "10px",
                      borderRadius: "8px",
                      marginBottom: "8px",
                      borderLeft: "5px solid #ff6b36",
                    }}
                  >
                    <strong style={{ color: "#f7e1c6", fontSize: "1rem" }}>
                      {key}
                    </strong>
                    <div style={{ marginTop: "4px", color: "#f0f0f0" }}>
                      {typeof value === "object" ? (
                        <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      ) : (
                        value.toString()
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <span>{msg.text}</span>
            )}
          </div>
        ))}
      </div>
      <input
        type="text"
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        placeholder="Ask your AI assistant..."
        style={{
          width: "100%",
          padding: "12px",
          fontSize: "16px",
          borderRadius: "8px",
          border: "1px solid #ccc",
          marginBottom: "12px",
        }}
      />
      <div style={{ display: "flex", gap: "10px", marginBottom: "1rem" }}>
        <div className="p-4 bg-yellow-100 rounded-xl max-w-sm mx-auto">
          <input type="file" onChange={handleFileChange} className="mb-2" />
          <button
            onClick={handleUpload}
            className="bg-orange-500 text-white px-4 py-2 rounded-lg"
          >
            Upload
          </button>
        </div>
        <button
          onClick={handleSubmit}
          style={{
            padding: "10px 20px",
            backgroundColor: "#ff6b36",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          Send
        </button>
        <button
          onClick={isRecording ? handleStopRecording : handleStartRecording}
          style={{
            padding: "10px 20px",
            backgroundColor: isRecording ? "#d32f2f" : "#1a659e",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          {isRecording ? <FaStop /> : <FaMicrophone />}
        </button>
      </div>
    </div>
  );
};

export default ConnectionTest;

//   return (
//     <div style={styles.container}>
//       <div style={styles.header}>
//         <h1 style={styles.title}>Chat with Assistant</h1>
//       </div>

//       <div style={styles.inputContainer}>
//         <input
//           type="text"
//           value={inputText}
//           onChange={(e) => setInputText(e.target.value)}
//           placeholder="Ask your AI assistant..."
//           style={styles.input}
//         />
//         <div style={styles.buttonGroup}>
//           <button onClick={handleSubmit} style={{ ...styles.button, ...styles.sendButton }} aria-label="Send message">
//             <FaPaperPlane />
//             <span>Send</span>
//           </button>
//           <button
//             onClick={isRecording ? handleStopRecording : handleStartRecording}
//             style={{
//               ...styles.button,
//               ...(isRecording ? styles.recordingButton : styles.recordButton),
//             }}
//             aria-label={isRecording ? "Stop recording" : "Start recording"}
//           >
//             {isRecording ? <FaStop /> : <FaMicrophone />}
//             <span>{isRecording ? "Stop" : "Record"}</span>
//           </button>
//         </div>
//       </div>

//       <div style={styles.uploadContainer}>
//         <div style={styles.fileInputWrapper}>
//           <input type="file" onChange={handleFileChange} id="file-upload" style={styles.fileInput} />
//           <label htmlFor="file-upload" style={styles.fileLabel}>
//             {file ? file.name : "Choose a file"}
//           </label>
//         </div>
//         <button
//           onClick={handleUpload}
//           style={{
//             ...styles.uploadButton,
//             ...(file ? {} : styles.disabledUploadButton),
//           }}
//           disabled={!file}
//         >
//           <FaUpload />
//           <span>Upload</span>
//         </button>
//       </div>

//       {/* Text Response */}
//       {rawTextResponse && (
//         <div style={{ ...styles.responseContainer, ...styles.textResponse }}>
//           <h3 style={styles.responseHeader}>Response</h3>
//           <div style={styles.responseContent}>
//             <p>{rawTextResponse}</p>
//           </div>
//         </div>
//       )}

//       {/* JSON Response */}
//       {responseData && (
//         <div style={{ ...styles.responseContainer, ...styles.jsonResponse }}>
//           <h3 style={styles.responseHeader}>Structured Response</h3>
//           <div style={styles.jsonItems}>
//             {Object.entries(responseData).map(([key, value]) => (
//               <div key={key} style={styles.jsonItem}>
//                 <div style={styles.jsonKey}>{key.replace(/_/g, " ")}</div>
//                 <div style={styles.jsonValue}>
//                   {Array.isArray(value) ? (
//                     <ul style={styles.jsonList}>
//                       {value.map((item, index) => (
//                         <li key={index} style={styles.jsonListItem}>
//                           {typeof item === "object" ? JSON.stringify(item) : item}
//                         </li>
//                       ))}
//                     </ul>
//                   ) : (
//                     <div>{typeof value === "object" ? JSON.stringify(value, null, 2) : value}</div>
//                   )}
//                 </div>
//               </div>
//             ))}
//           </div>
//         </div>
//       )}
//     </div>
//   )
// };
// Styles
const styles = {
  container: {
    maxWidth: "800px",
    margin: "2rem auto",
    padding: "2rem",
    fontFamily:
      "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    backgroundColor: "#1a1a1a",
    color: "#e0e0e0",
    borderRadius: "16px",
    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
  },
  header: {
    marginBottom: "2rem",
    textAlign: "center",
  },
  title: {
    fontSize: "2.2rem",
    fontWeight: "700",
    color: "#ff6b36",
    margin: "0",
    textShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
  },
  inputContainer: {
    marginBottom: "1.5rem",
  },
  input: {
    width: "100%",
    padding: "1rem 1.25rem",
    fontSize: "1rem",
    border: "2px solid #333",
    borderRadius: "12px",
    backgroundColor: "#2a2a2a",
    color: "#e0e0e0",
    transition: "all 0.2s ease",
    marginBottom: "1rem",
    boxSizing: "border-box",
  },
  buttonGroup: {
    display: "flex",
    gap: "1rem",
  },
  button: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0.5rem",
    padding: "0.75rem 1.5rem",
    fontSize: "0.95rem",
    fontWeight: "600",
    border: "none",
    borderRadius: "10px",
    cursor: "pointer",
    transition: "all 0.2s ease",
    flex: 1,
  },
  sendButton: {
    backgroundColor: "#ff6b36",
    color: "white",
  },
  recordButton: {
    backgroundColor: "#1a659e",
    color: "white",
  },
  recordingButton: {
    backgroundColor: "#d32f2f",
    color: "white",
    animation: "pulse 1.5s infinite",
  },
  uploadContainer: {
    display: "flex",
    alignItems: "center",
    gap: "1rem",
    marginBottom: "2rem",
    padding: "1.25rem",
    backgroundColor: "#2a2a2a",
    borderRadius: "12px",
    border: "1px solid #333",
  },
  fileInputWrapper: {
    position: "relative",
    flex: 1,
  },
  fileInput: {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    opacity: 0,
    cursor: "pointer",
  },
  fileLabel: {
    display: "block",
    padding: "0.75rem 1rem",
    backgroundColor: "#333",
    border: "1px solid #444",
    borderRadius: "8px",
    fontSize: "0.9rem",
    color: "#e0e0e0",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    cursor: "pointer",
  },
  uploadButton: {
    backgroundColor: "#f59e0b",
    color: "white",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0.5rem",
    padding: "0.75rem 1.5rem",
    fontSize: "0.95rem",
    fontWeight: "600",
    border: "none",
    borderRadius: "10px",
    cursor: "pointer",
    transition: "all 0.2s ease",
  },
  disabledUploadButton: {
    backgroundColor: "#555",
    cursor: "not-allowed",
  },
  responseContainer: {
    marginTop: "2rem",
    borderRadius: "12px",
    overflow: "hidden",
    border: "1px solid #333",
  },
  responseHeader: {
    margin: 0,
    padding: "1rem",
    fontSize: "1.1rem",
    fontWeight: "600",
    backgroundColor: "#333",
    color: "#e0e0e0",
  },
  textResponse: {
    backgroundColor: "#2a2a2a",
  },
  responseContent: {
    padding: "1rem",
    lineHeight: "1.6",
    color: "#e0e0e0",
  },
  jsonResponse: {
    backgroundColor: "#2a2a2a",
  },
  jsonItems: {
    padding: "0.5rem",
  },
  jsonItem: {
    marginBottom: "1rem",
    backgroundColor: "#333",
    border: "1px solid #444",
    borderRadius: "8px",
    overflow: "hidden",
  },
  jsonKey: {
    padding: "0.75rem 1rem",
    backgroundColor: "#444",
    fontWeight: "600",
    textTransform: "capitalize",
    color: "#e0e0e0",
    borderBottom: "1px solid #555",
  },
  jsonValue: {
    padding: "1rem",
    backgroundColor: "#333",
    color: "#e0e0e0",
    fontFamily: "'Menlo', 'Monaco', 'Courier New', monospace",
    fontSize: "0.9rem",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  jsonList: {
    margin: 0,
    paddingLeft: "1.5rem",
    color: "#e0e0e0",
  },
  jsonListItem: {
    marginBottom: "0.5rem",
  },
};
