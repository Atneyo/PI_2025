# YOLO Detection Helper

Ce dossier contient un unique script `yolo_detection.py` ainsi que le modèle `yolov11n.hef`. Ce script remplace totalement toute logique de parsing CLI compliquée : il expose une seule fonction Python `yolo_detection(...)` et quelques constantes faciles à modifier.

## Structure générale

- **Constantes (lignes 25‑54)** : définissent les chemins (dossier, fichier HEF par défaut) et les "knobs" les plus courants (FPS, webcam ou vidéo, nom du fichier enregistré, etc.). Il suffit de modifier ces variables pour changer le comportement global.
- **`FixedArgsParser` + `_runtime_namespace()`** : Hailo attend un objet `argparse`. On lui fournit une version minimaliste qui retourne simplement un `SimpleNamespace` regroupant les paramètres essentiels (source vidéo, FPS, archi, etc.). Aucun parsing n'est nécessaire.
- **`_recording_output_path()`** : crée le dossier d'enregistrement (par défaut `recordings/`) et retourne le chemin final du MKV. Si aucun nom n'est fourni, il génère un timestamp.
- **Enregistrement sûr** : la vidéo est d'abord écrite dans un fichier temporaire `<nom>.part`, puis renommée à la fin uniquement si des données ont bien été écrites (pas de fichier 0 octet).
- **Gestion `.part`** : l'enregistrement se fait d'abord dans un fichier temporaire `<nom>.part`, renommé seulement après la fin du pipeline. Cela évite de servir un fichier partiel/0 ko.
- **`UserCallback`** : collecte quelques statistiques (nombre d'images, FPS moyen, nombre de détections) et imprime un résumé à la fin.
- **`RecordingDetectionApp`** : c'est la classe qui construit le pipeline GStreamer. Elle étend `GStreamerDetectionApp` et ajoute une branche qui encode l'image annotée en `matroskamux -> filesink`. Tout est vidéo uniquement (pas d'audio) pour rester simple.
  - La méthode `get_pipeline_string()` assemble les blocs Hailo/GStreamer dans l'ordre exact attendu :
    1. `SOURCE_PIPELINE` prend la vidéo (fichier ou webcam) et la met au bon format.
    2. `INFERENCE_PIPELINE` + `INFERENCE_PIPELINE_WRAPPER` charge le modèle `*.hef` et exécute la détection sur la puce Hailo.
    3. `TRACKER_PIPELINE` applique un tracking simple (ID par classe 1).
    4. `USER_CALLBACK_PIPELINE` insère le hook Python (`app_callback`) pour compter les détections / stats.
    5. `tee` duplique le flux : une branche va vers `DISPLAY_PIPELINE` (affichage) et l'autre passe dans `_record_video_branch()` puis `matroskamux` pour sauvegarder le MKV.
  - Cet ordre est imposé par la stack Hailo : la détection doit recevoir la source brute, produire des ROIs, puis seulement après on peut tracker, overlay et encoder.
- **`load_detection_environment()`** : charge le `.env` local attendu par les libs Hailo et affiche son contenu pour vérification.
- **`yolo_detection()`** : point d'entrée principal. On lui passe `live_input=True` pour la webcam, `False` avec `video_path="..."` pour lire un fichier. Il prépare la configuration (FPS, fichier HEF, chemin d'enregistrement), lance le pipeline et retourne le chemin du MKV produit.
  - Paramètre `display_window`: `False` par défaut pour un mode headless. Passez `True` si vous voulez voir la fenêtre `autovideosink`.

## Pourquoi ce design ?

- **Pas de CLI** : les anciens scripts Hailo reposaient sur `argparse`. Ici on veut un appel direct depuis FastAPI/ Python. D'où le `FixedArgsParser` qui ne fait qu'encapsuler des valeurs déjà connues.
- **Paramètres lisibles** : toutes les options importantes sont en haut du fichier. Pas besoin de fouiller d'autres modules ou de comprendre `argparse`.
- **Pipeline vidéo unique** : l'objectif est uniquement de sauvegarder le flux YOLO annoté. L'audio, la capture avancée, etc. ont été retirés pour garder un pipeline court et facile à lire.
- **Fonction unique** : `yolo_detection()` lance le pipeline et renvoie le fichier. On peut l'appeler depuis `main.py` après avoir reçu un upload, ou depuis n'importe quel autre script.

## Comment l'utiliser

```python
from interface.backend.AI.yolo_detection import yolo_detection

# Exemple : lancer une détection sur un fichier uploadé en visant 15 FPS
result_path = yolo_detection(
    live_input=False,
    video_path="uploads/video.mp4",
    frame_rate=15,
    hef_path="interface/backend/AI/yolov11n.hef",
    output_dir="interface/backend/outputs",
    record_filename="result.webm",
    display_window=False,  # désactive l'affichage si besoin
)
print("Fichier annoté :", result_path)
```

Le script s’occupe automatiquement de :

1. Charger l’environnement Hailo via `.env`.
2. Construire le pipeline (source -> inference -> tracker -> overlay -> display + enregistrement MKV).
3. Afficher des logs simples (stats et résumé final).
4. Libérer correctement les ressources.

## Ajustements fréquents

- **Changer la source par défaut** : modifiez `USE_WEBCAM` ou `DEFAULT_VIDEO` dans les constantes.
- **Modifier le dossier/nom d’enregistrement** : mettez à jour `RECORD_FILENAME` ou passez `record_filename="..."` lors de l’appel.
- **Personnaliser FPS ou HEF** : changez `FRAME_RATE` / `HEF_FILE` en haut, ou passez `frame_rate=` / `hef_path=` à `yolo_detection()`.
- **Désactiver l’enregistrement** : appelez `yolo_detection(..., enable_recording=False)` pour juste afficher le flux.

En résumé : ce script est volontairement minimaliste pour être intégré facilement dans le backend FastAPI. Aucune commande externe n’est nécessaire, tout se configure via les paramètres ou les constantes en haut du fichier.
