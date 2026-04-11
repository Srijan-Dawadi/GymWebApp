# face-api.js Model Files

Download the following model files from:
https://github.com/justadudewhohacks/face-api.js/tree/master/weights

Required files (place all in this directory):

## ssd_mobilenetv1
- ssd_mobilenetv1_model-weights_manifest.json
- ssd_mobilenetv1_model-shard1
- ssd_mobilenetv1_model-shard2

## face_landmark_68
- face_landmark_68_model-weights_manifest.json
- face_landmark_68_model-shard1

## face_recognition
- face_recognition_model-weights_manifest.json
- face_recognition_model-shard1
- face_recognition_model-shard2

## Quick download (run from project root):
```bash
mkdir -p static/face-api/models
cd static/face-api/models

BASE=https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights

for f in ssd_mobilenetv1_model-weights_manifest.json ssd_mobilenetv1_model-shard1 ssd_mobilenetv1_model-shard2 \
          face_landmark_68_model-weights_manifest.json face_landmark_68_model-shard1 \
          face_recognition_model-weights_manifest.json face_recognition_model-shard1 face_recognition_model-shard2; do
  curl -O "$BASE/$f"
done
```
