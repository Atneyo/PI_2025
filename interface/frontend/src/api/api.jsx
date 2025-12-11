export async function analyzeVideo(files) {
  const formData = new FormData();

  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  const response = await fetch("http://127.0.0.1:8000/analyze-video/", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Error during analyze");
  }

  return await response.json();
}

export async function analyzeAudio(files) {
  const formData = new FormData();

  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  const response = await fetch("http://127.0.0.1:8000/analyze-audio/", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Error during analyze");
  }

  return await response.json();
}
