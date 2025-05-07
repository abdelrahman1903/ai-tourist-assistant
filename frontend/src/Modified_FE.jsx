import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { FaMicrophone, FaStop, FaPaperPlane, FaSpinner } from "react-icons/fa";

const ConnectionTest = () => {
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState([]); // Holds all messages (both user and assistant)
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false); // New state for loading indicator
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const [file, setFile] = useState(null);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const messagesEndRef = useRef(null);
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setFile(e.target.files[0]);
      setShowFileUpload(true);
    }
  };

  const clearFile = () => {
    setFile(null);
    setShowFileUpload(false);
    // Reset the file input
    const fileInput = document.getElementById("file-input");
    if (fileInput) fileInput.value = "";
  };

  const handleUpload = async (userMessage) => {
    if (!file || !userMessage) return;
    setIsLoading(true); // Show loading indicator
    const formData = new FormData();
    formData.append("file", file);
    formData.append("message", JSON.stringify(userMessage.text)); // ⬅️ Add user message here
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
      // Reset file state after successful upload
      clearFile();
      // console.log("Upload successful:", response.data);
      return response;
      
    } catch (error) {
      console.error("Upload error:", error);
    } finally {
      setIsLoading(false); // Hide loading indicator
    }
  };

  const handleSubmit = async () => {
    if (!inputText.trim() || isLoading) return;
    // Upload file if selected
    setIsLoading(true); // Show loading indicator
    let response;
    let loadingMessageId;
    const userMessage = { type: "user", text: inputText };
    if (file) {
      try {
        const fileInMessage = { type: "user", text: `📄 Uploaded File: \n${file.name}`};
        setMessages((prev) => [...prev, fileInMessage]);
        setMessages((prev) => [...prev, userMessage]);
        setInputText(""); // Clear input
        // Add a temporary loading message
        loadingMessageId = Date.now();
        setMessages((prev) => [
          ...prev,
          {
            id: loadingMessageId,
            type: "assistant",
            text: "...",
            isLoading: true,
          },
        ]);
        response = await handleUpload(userMessage); // wait for file to upload
        console.log("testing response: "+response.data)
      } catch (err) {
        console.error("File upload failed. Stopping submit.");
        setIsLoading(false);
        return; // Stop if upload failed
      }
    } else {
      try {
        setMessages((prev) => [...prev, userMessage]);
        setInputText(""); // Clear input
        // Add a temporary loading message
        loadingMessageId = Date.now();
        setMessages((prev) => [
          ...prev,
          {
            id: loadingMessageId,
            type: "assistant",
            text: "...",
            isLoading: true,
          },
        ]);
        response = await axios.post("http://127.0.0.1:8000/chat", {
          text: inputText,
        });
      } catch (err) {
        console.error("message upload failed. Stopping submit.");
        setIsLoading(false);
        return; // Stop if upload failed
      }
    }

    try {
      // Remove the loading message
      setMessages((prev) => prev.filter((msg) => msg.id !== loadingMessageId));
      let parsed;
      let assistantMessage;
      // console.log("test"+response)
      try {
        parsed = JSON.parse(response.data.response); // try to parse JSON
        assistantMessage = {
          type: "assistant",
          text: parsed,
          isJson: true,
        };
      } catch (err) {
        assistantMessage = {
          type: "assistant",
          text: response.data.response,
          isJson: false,
        };
      }
      // console.log(assistantMessage)
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending data:", error);
      // Add error message
      setMessages((prev) => [
        ...prev.filter((msg) => msg.id !== loadingMessageId),
        { type: "error", text: "Failed to get response. Please try again." },
      ]);
    } finally {
      setIsLoading(false); // Hide loading indicator
    }
  };

  const handleStartRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    mediaRecorderRef.current = new MediaRecorder(stream);
    chunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    mediaRecorderRef.current.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "audio/wav" });
      uploadAudio(blob);
    };

    mediaRecorderRef.current.start();
    setIsRecording(true);
  };

  const handleStopRecording = () => {
    setIsLoading(true); // Show loading indicator
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const uploadAudio = async (blob) => {
    const formData = new FormData();
    formData.append("audio", blob, "recording.wav");

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
      setInputText(response.data.Transcription);
    } catch (error) {
      console.error("Error uploading audio:", error);
    } finally {
      setIsLoading(false); // Hide loading indicator
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div style={styles.chatContainer}>
      <div style={styles.chatInterface}>
        <h1 style={styles.chatTitle}>Chat with Assistant</h1>

        {/* Messages area */}
        <div style={styles.messagesArea} className="custom-scrollbar">
          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                ...styles.message,
                ...(msg.type === "user"
                  ? styles.userMessage
                  : msg.type === "error"
                  ? styles.errorMessage
                  : styles.assistantMessage),
                ...(msg.isLoading ? styles.loadingMessage : {}),
              }}
            >
              {msg.isLoading ? (
                // Improved loading indicator
                <div style={styles.loadingIndicator}>
                  <div style={styles.typingDots}>
                    <span style={styles.dot}></span>
                    <span style={styles.dot}></span>
                    <span style={styles.dot}></span>
                  </div>
                </div>
              ) : msg.isJson ? (
                <div style={styles.jsonContent}>
                  {Object.entries(msg.text).map(([key, value], idx) => (
                    <div key={idx} style={styles.jsonItem}>
                      <div style={styles.jsonKey}>{key}</div>
                      <div style={styles.jsonValue}>
                        {typeof value === "object" ? (
                          <pre style={styles.jsonValuePre}>
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
          {/* Element for auto-scrolling */}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div style={styles.inputArea}>
          <div style={styles.inputContainer}>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="type your text here"
              style={{
                ...styles.textInput,
                ...(isLoading ? styles.disabledInput : {}),
              }}
              disabled={isLoading}
            />

            <div style={styles.buttonRow}>
              {!showFileUpload ? (
                <div style={styles.chooseFileBtn}>
                  <input
                    type="file"
                    id="file-input"
                    onChange={handleFileChange}
                    style={styles.hiddenInput}
                    disabled={isLoading}
                  />
                  <label
                    htmlFor="file-input"
                    style={{
                      ...styles.fileLabel,
                      ...(isLoading ? styles.disabledLabel : {}),
                    }}
                  >
                    choose file
                  </label>
                </div>
              ) : (
                <div style={styles.fileInfo}>
                  <div style={styles.fileName}>{file?.name || "file name"}</div>
                  <div style={styles.fileActions}>
                    <button
                      onClick={clearFile}
                      style={{
                        ...styles.cancelButton,
                        ...(isLoading ? styles.disabledButton : {}),
                      }}
                      disabled={isLoading}
                    >
                      cancel
                    </button>
                    <button
                      onClick={handleUpload}
                      style={{
                        ...styles.uploadButton,
                        ...(isLoading ? styles.disabledButton : {}),
                      }}
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <div style={styles.buttonLoader}>
                          <FaSpinner style={styles.spinnerIcon} />
                        </div>
                      ) : (
                        "upload"
                      )}
                    </button>
                  </div>
                </div>
              )}

              <div style={styles.actionButtons}>
                <button
                  onClick={
                    isRecording ? handleStopRecording : handleStartRecording
                  }
                  style={{
                    ...styles.actionButton,
                    ...(isRecording
                      ? styles.recordingButton
                      : styles.micButton),
                    ...(isLoading && !isRecording ? styles.disabledButton : {}),
                  }}
                  disabled={isLoading && !isRecording}
                  aria-label={
                    isRecording ? "Stop recording" : "Start recording"
                  }
                >
                  {isRecording ? <FaStop /> : <FaMicrophone />}
                  <span>mic</span>
                </button>

                <button
                  onClick={handleSubmit}
                  style={{
                    ...styles.actionButton,
                    ...styles.sendButton,
                    ...(!inputText.trim() || isLoading
                      ? styles.disabledButton
                      : {}),
                  }}
                  disabled={!inputText.trim() || isLoading}
                  aria-label="Send message"
                >
                  {isLoading ? (
                    <div style={styles.buttonLoader}>
                      <FaSpinner style={styles.spinnerIcon} />
                    </div>
                  ) : (
                    <FaPaperPlane />
                  )}
                  <span>send</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Add custom scrollbar styles */}
      <style
        dangerouslySetInnerHTML={{
          __html: `
          .custom-scrollbar::-webkit-scrollbar {
            width: 8px;
            height: 8px;
          }
          .custom-scrollbar::-webkit-scrollbar-track {
            background: #2a2a2a;
            border-radius: 4px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 4px;
            border: 2px solid #2a2a2a;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: #777;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(211, 47, 47, 0); }
            100% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0); }
          }
          @keyframes blink {
            0% { opacity: 0.4; }
            20% { opacity: 1; }
            100% { opacity: 0.4; }
          }
        `,
        }}
      />
    </div>
  );
};

const styles = {
  chatContainer: {
    width: "100%",
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#000000",
    color: "#e0e0e0",
    fontFamily:
      "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    padding: 0,
    margin: 0,
    overflow: "hidden",
  },
  chatInterface: {
    display: "flex",
    flexDirection: "column",
    width: "100%",
    maxWidth: "800px",
    height: "80vh", // Fixed height for better scrolling
    backgroundColor: "#1a1a1a",
    borderRadius: "16px",
    overflow: "hidden",
    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
    padding: "1.5rem",
    margin: "1rem",
  },
  chatTitle: {
    fontSize: "1.8rem",
    fontWeight: 700,
    color: "#ff6b36",
    textAlign: "center",
    margin: "0 0 1.5rem 0",
  },
  // HIGHLIGHT: Improved messages area with better scrolling
  messagesArea: {
    display: "flex",
    flexDirection: "column",
    gap: "1rem",
    marginBottom: "1.5rem",
    flex: 1, // Take available space
    overflowY: "auto",
    paddingRight: "0.75rem", // More space for scrollbar
    paddingLeft: "0.25rem",
  },
  message: {
    padding: "1rem",
    borderRadius: "12px",
    maxWidth: "85%",
    wordBreak: "break-word",
  },
  userMessage: {
    alignSelf: "flex-end",
    backgroundColor: "#333333",
    borderBottomRightRadius: "4px",
    whiteSpace: "pre-line"
  },
  assistantMessage: {
    alignSelf: "flex-start",
    backgroundColor: "#2a2a2a",
    borderBottomLeftRadius: "4px",
  },
  // HIGHLIGHT: Added error message style
  errorMessage: {
    alignSelf: "flex-start",
    backgroundColor: "#5c2626",
    borderBottomLeftRadius: "4px",
    color: "#ffcccc",
  },
  // HIGHLIGHT: Improved loading message style
  loadingMessage: {
    backgroundColor: "#2a2a2a",
    opacity: 0.9,
    minWidth: "80px",
    minHeight: "40px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  // HIGHLIGHT: New loading indicator with typing animation
  loadingIndicator: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    height: "100%",
  },
  // HIGHLIGHT: Typing dots animation
  typingDots: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "4px",
  },
  // HIGHLIGHT: Individual dot for typing animation
  dot: {
    width: "8px",
    height: "8px",
    backgroundColor: "#e0e0e0",
    borderRadius: "50%",
    display: "inline-block",
    animation: "blink 1.4s infinite both",
    animationDelay: "calc(var(--i) * 0.2s)",
  },
  // HIGHLIGHT: Spinner icon for buttons
  spinnerIcon: {
    animation: "spin 1s linear infinite",
    fontSize: "0.85rem",
  },
  jsonContent: {
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
  },
  jsonItem: {
    backgroundColor: "#333",
    borderRadius: "8px",
    overflow: "hidden",
    border: "1px solid #444",
  },
  jsonKey: {
    padding: "0.75rem 1rem",
    backgroundColor: "#444",
    fontWeight: 600,
    color: "#f7e1c6",
    borderBottom: "1px solid #555",
  },
  jsonValue: {
    padding: "0.75rem 1rem",
    color: "#f0f0f0",
    fontFamily: "'Menlo', 'Monaco', 'Courier New', monospace",
    fontSize: "0.9rem",
  },
  jsonValuePre: {
    margin: 0,
    whiteSpace: "pre-wrap",
  },
  inputArea: {
    marginTop: "auto",
    width: "100%",
  },
  inputContainer: {
    display: "flex",
    flexDirection: "column",
    backgroundColor: "#333333",
    borderRadius: "12px",
    padding: "0.75rem",
    gap: "0.75rem",
    border: "1px solid #444",
    width: "100%",
    boxSizing: "border-box",
  },
  textInput: {
    width: "100%",
    padding: "0.75rem",
    fontSize: "1rem",
    border: "none",
    backgroundColor: "#3a3a3a",
    color: "#e0e0e0",
    borderRadius: "8px",
    minHeight: "24px",
    boxSizing: "border-box",
  },
  // HIGHLIGHT: Added disabled input style
  disabledInput: {
    backgroundColor: "#2d2d2d",
    color: "#999",
    cursor: "not-allowed",
  },
  buttonRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "0.75rem",
    width: "100%",
  },
  hiddenInput: {
    position: "absolute",
    width: "1px",
    height: "1px",
    padding: 0,
    margin: "-1px",
    overflow: "hidden",
    clip: "rect(0, 0, 0, 0)",
    whiteSpace: "nowrap",
    borderWidth: 0,
  },
  chooseFileBtn: {
    flexShrink: 0,
  },
  fileLabel: {
    display: "inline-block",
    padding: "0.5rem 0.75rem",
    backgroundColor: "#3a3a3a",
    border: "1px solid #444",
    borderRadius: "8px",
    fontSize: "0.9rem",
    color: "#e0e0e0",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  // HIGHLIGHT: Added disabled label style
  disabledLabel: {
    backgroundColor: "#2d2d2d",
    color: "#999",
    cursor: "not-allowed",
  },
  fileInfo: {
    display: "flex",
    flexDirection: "column",
    backgroundColor: "#3a3a3a",
    border: "1px solid #444",
    borderRadius: "8px",
    overflow: "hidden",
    minWidth: "150px",
  },
  fileName: {
    padding: "0.5rem 0.75rem",
    color: "#e0e0e0",
    fontSize: "0.9rem",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    maxWidth: "200px",
    borderBottom: "1px solid #444",
  },
  fileActions: {
    display: "flex",
    width: "100%",
  },
  cancelButton: {
    padding: "0.4rem 0.6rem",
    fontSize: "0.85rem",
    border: "none",
    cursor: "pointer",
    flex: 1,
    textAlign: "center",
    width: "50%",
    boxSizing: "border-box",
    backgroundColor: "#3a3a3a",
    color: "#e0e0e0",
    borderRight: "1px solid #444",
  },
  uploadButton: {
    padding: "0.4rem 0.6rem",
    fontSize: "0.85rem",
    border: "none",
    cursor: "pointer",
    flex: 1,
    textAlign: "center",
    width: "50%",
    boxSizing: "border-box",
    backgroundColor: "#f59e0b",
    color: "white",
  },
  actionButtons: {
    display: "flex",
    gap: "0.5rem",
    marginLeft: "auto",
  },
  actionButton: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0.3rem",
    padding: "0.5rem 0.75rem",
    fontSize: "0.85rem",
    border: "1px solid #444",
    borderRadius: "8px",
    cursor: "pointer",
    transition: "all 0.2s ease",
  },
  micButton: {
    backgroundColor: "#1a659e",
    color: "white",
    borderColor: "#1a659e",
  },
  recordingButton: {
    backgroundColor: "#d32f2f",
    borderColor: "#d32f2f",
    color: "white",
    animation: "pulse 1.5s infinite",
  },
  sendButton: {
    backgroundColor: "#ff6b36",
    color: "white",
    borderColor: "#ff6b36",
  },
  // HIGHLIGHT: Improved disabled button style
  disabledButton: {
    backgroundColor: "#444",
    borderColor: "#555",
    color: "#999",
    cursor: "not-allowed",
    opacity: 0.7,
  },
  // HIGHLIGHT: Added button loader container
  buttonLoader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
};

export default ConnectionTest;
