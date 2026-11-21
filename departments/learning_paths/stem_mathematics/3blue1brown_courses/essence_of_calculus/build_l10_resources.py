import os
import json

base_dir = r"D:\0PEN CODE\Dub Studio"

# Target paths
script_dir = os.path.join(base_dir, r"departments\learning_paths\stem_mathematics\3blue1brown_courses\essence_of_calculus\lesson_10_taylor_series\dubbing_pipeline")
audio_dir = os.path.join(base_dir, r"departments\learning_paths\stem_mathematics\3blue1brown_courses\web_platform\assets\audio\calculus\lesson_10")
data_dir = os.path.join(base_dir, r"departments\learning_paths\stem_mathematics\3blue1brown_courses\web_platform\data\calculus")

os.makedirs(script_dir, exist_ok=True)
os.makedirs(audio_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

print("Directories verified/created.")
