# Industrial Project (2025-2026)

## Project Overview

This project studies different artificial intelligence models for computer vision and Speech-to-Text on audio and video files. The models will be run on a Raspberry Pi 5, allowing performance comparison, with and without the AI accelerator (Hailo AI HAT), and will include a human-machine interface for result visualization.

## Project Goals

The objectives of this project are:

* Use various AI models to detect objects in videos, either in real-time or in imported videos
* Use various AI models to convert audio to text (Speech-to-Text) from video and audio files, either in real-time or from imported files
* Run the models on a Raspberry Pi 5
* Develop a human-machine interface allowing the selection of different test parameters (model used, number of fps, choice of a specific temporal study zone in a video, with or without the accelerator) and videos (real-time camera usage or drag-and-drop video import) and display the results
* Compare the different models used, with and without the Hailo AI HAT accelerator
* Provide a single-command, offline executable application

## Project Structure

```text
/
├── README.md                       # Main project README
│
├── interface/
│   ├── README.md
│   ├── frontend/                   # User interface
│   │   ├── src/                    # Frontend source code
│   │   │   ├── pages/              # Full pages (route-level views)
│   │   │   └── components/         # Reusable UI components
│   │
│   └── backend/                    # Backend connecting the interface with the models
│
├── models/                         # AI Models (CV and STT)
│   ├── README.md
│   ├── computer_vision/            # Object detection models
│   └── speech_to_text/             # Speech-to-Text models
│
├── monitoring/                     # Monitoring and performance metrics
│   ├── README.md
│
├── tests/                          # Tests and research experiments
│   ├── README.md
│
└── docs/                           # Additional documentation, diagrams, notes
```

## Installation Instructions

## Launch
(specify how to launch each component / provide a link to the corresponding README)

