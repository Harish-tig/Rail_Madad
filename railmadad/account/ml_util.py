# Testing code for Model 3

import tensorflow.lite as tflite
import numpy as np
from keras._tf_keras.keras.preprocessing import image
import os

# Load the proper class names from your saved file
class_names_path = r"/railmadad/ml_model/class_names.txt"
with open(class_names_path, "r") as f:
    class_names = [line.strip() for line in f.readlines()]

print("Using these class names:", class_names)

# Load the TFLite model
interpreter = tflite.Interpreter(model_path=r"/railmadad/ml_model/model.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Added: Dictionary to map categories to their respective classes
CATEGORY_MAP = {
    "Security": ["fire smoke", "trackdefective"],
    "Medical": ["medical assist"],
    "Cleanliness": ["unclean_coach"],
    "Electrical": ["defective switch"],
    "General": ["overcrowding"],
    "Not a Complaint": ["tracknotdefective", "clean coach", "normal", "non defective switch"],
    # "Coach Maintenance":["broken window","broken door","torn bed"]
}


# function to general model output into categories
def general_output(predicted_class):
    predicted_class = predicted_class.lower()
    for category, class_list in CATEGORY_MAP.items():
        if predicted_class in class_list:
            return {"category": category, "subcategory": predicted_class}


def predict_image(img_path):
    # Load and preprocess image exactly as in training
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)

    # Apply the EXACT SAME preprocessing as during training
    img_array = img_array / 127.5 - 1  # MobileNetV2 preprocessing

    # Run inference
    interpreter.set_tensor(input_details[0]['index'], img_array)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])

    # Get predicted class and confidence
    predicted_class = np.argmax(output[0])
    confidence = output[0][predicted_class]

    # Print all class probabilities for debugging
    for i, prob in enumerate(output[0]):
        print(f"  {class_names[i]}: {prob:.4f}")

    return predicted_class, confidence


# Test multiple images
test_images = [
   #  r"C:\Users\nadar\Downloads\Broken-rail.png",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\broken railway_track.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\clean_coach.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\coach clean.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\dirty coach.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\dirty_coach.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\fire in train.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\fire train.jpg",
   # r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\normal track.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\normal_arm.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\smalll fire.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\track fire.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\vb fire.jpg",
   #  r"C:\College\dsmlcourse\DSML projects\dataset\backup\test data\wound_test.jpg"
    ]

# for img_path in test_images:
#     print(f"\nPredicting: {os.path.basename(img_path)}")
#     predicted_class, confidence = predict_image(img_path)
#     predicted_class_name = class_names[predicted_class]
#     print(f"Predicted class: {predicted_class_name}")
#     print(f"Confidence: {confidence:.4f}")
#
#     # Get the generalized category
#     result = general_output(predicted_class_name)
#     print(f"Category: {result['category']}")
#     print(f"Subcategory: {result['subcategory']}")