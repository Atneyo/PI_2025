const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

export async function analyzeVideo(files) {
  const formData = new FormData();

  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  const response = await fetch(`${BACKEND_URL}/analyze-video/`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Error during analyze");
  }

  return await response.json();
}

export async function analyzeAudio(files) {
  console.log(BACKEND_URL)

  const formData = new FormData();

  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  const response = await fetch(`${BACKEND_URL}/analyze-audio/`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Error during analyze");
  }

  return await response.json();
}

export async function getMonitoring() {
  const response = await fetch(`${BACKEND_URL}/monitoring/`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Error during analyze");
  }

  return await response.json();
}