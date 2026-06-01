import axios from "axios";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`;

export async function analyzeJob(resumeFile, jdText) {
  const formData = new FormData();
  formData.append("resume_file", resumeFile);
  formData.append("jd_text", jdText);

  const response = await axios.post(`${API_BASE}/api/analyze`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
}
