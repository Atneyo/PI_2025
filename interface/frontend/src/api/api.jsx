export async function uploadFiles(files) {
  const formData = new FormData();

  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  const response = await fetch("http://127.0.0.1:8000/uploadfiles/", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Error during upload");
  }

  return await response.json();
}
