import React, { useState, useRef } from "react";
import { FaMicrophone, FaStop } from "react-icons/fa";
import axios from "axios";

const AudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const handleStartRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); //Asks the user to allow access to the microphone, Returns an audio stream

    mediaRecorderRef.current = new MediaRecorder(stream);
    chunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (event) => { //Every time the browser has some recorded audio ready, this callback runs
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    mediaRecorderRef.current.onstop = () => { //Combines all chunks into a single audio file
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

  const uploadAudio = async (blob) => { //send audio to the server
    const formData = new FormData();
    formData.append("audio", blob, "recording.wav");
    console.log(blob.type); // from React
    try {
      const response = await axios.post("http://127.0.0.1:8000/audio", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

    //   const data = await response.json();
      console.log("Transcription:", response.data.Transcription);
    } catch (error) {
      console.error("Error uploading audio:", error);
    }
  };

  return (
    <button onClick={isRecording ? handleStopRecording : handleStartRecording}>
      {isRecording ? <FaStop /> : <FaMicrophone />}
    </button>
  );
};

export default AudioRecorder;
