# Para-Site-Installation

## Before Clone
[Install Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage)

Para Site TouchDesigner installation project.

## File structure

```
Para-Site-Installation/
├── README.md
├── .gitignore
├── .gitattributes
│
├── Para-Site-Installation.toe    # Main installation project
├── Effect-Test.toe               # Effect test project
├── Old-Project.toe               # Legacy project file
│
├── assets/                       # Media assets (video clips)
│   └── Put all media files here
│
├── toxes/                        # TouchDesigner components (.tox) and their project files (.toe)
│   ├── BitmapEffect.toe / .tox
│   ├── BasicGlitch.toe / .tox
│   ├── QuantizeAndNoise.toe / .tox
│   ├── SpectralPointCloud.toe / .tox
│   ├── BlobTracking.toe / .tox
│   ├── DataMoshing.toe / .tox  (and Datamosh.toe)
│   ├── GlitchNoiseAndEdge.toe / .tox
│   ├── CrtScanline.toe / .tox
│   └── MediaPipe/                # MediaPipe-based operators
│       ├── MediaPipe.tox
│       ├── face_detector.tox, face_tracking.tox, face_filter_example.tox, face_mapping_example.tox
│       ├── hand_tracking.tox, pose_tracking.tox, object_tracking.tox
│       ├── image_classification.tox, image_embeddings.tox
│       └── (corresponding .toe examples as present)
│
├── _obsolete/                    # Ignored: deprecated project files (e.g. Pixelate.toe)
└── Backup/                       # Ignored: backup files
```
