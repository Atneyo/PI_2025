from hailort import Device, InferVStreams, HEF, ConfigureParams
import cv2
import numpy as np

HEF_PATH = "model.hef"
VIDEO_PATH = "input.mp4"

# Charger le modèle HEF
hef = HEF(HEF_PATH)

# Ouvrir le device Hailo
with Device() as device:
    # Configure network
    configure_params = ConfigureParams.create_from_hef(hef, device)
    network_group = device.configure(hef, configure_params)

    # Get input / output streams
    input_vstreams = InferVStreams.create_input_vstreams(network_group)
    output_vstreams = InferVStreams.create_output_vstreams(network_group)

    input_name = list(input_vstreams.keys())[0]
    output_name = list(output_vstreams.keys())[0]

    cap = cv2.VideoCapture(VIDEO_PATH)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Prétraitement image
        img_resized = cv2.resize(frame, (640, 640))
        img = img_resized.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)
        img = img[np.newaxis, ...]

        # Envoyer image → Hailo
        input_vstreams[input_name].send(img)

        # Récupérer sortie
        output_data = output_vstreams[output_name].recv()

        # DEBUG : afficher forme sortie
        print("Output shape:", output_data.shape)

        # Ici tu peux ajouter ton post-traitement YOLO
        cv2.imshow("frame", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
