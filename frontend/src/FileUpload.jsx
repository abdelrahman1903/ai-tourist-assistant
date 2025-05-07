import React, { useState } from "react";
import axios from "axios";

const FileUpload = () => {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:8000/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      // console.log("Upload successful:", response.data);
      return response.data
    } catch (error) {
      console.error("Upload error:", error);
    }
  };

  return (
    <div className="p-4 bg-yellow-100 rounded-xl max-w-sm mx-auto">
      <input type="file" onChange={handleFileChange} className="mb-2" />
      <button
        onClick={handleUpload}
        className="bg-orange-500 text-white px-4 py-2 rounded-lg"
      >
        Upload
      </button>
    </div>
  );
};

export default FileUpload;