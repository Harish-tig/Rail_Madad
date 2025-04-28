import os
import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from uuid import uuid4
from .app_mail import register_email, raise_complaint_mail
from .utils import decoder
from rest_framework.decorators import api_view
from django.http import JsonResponse
import numpy as np
import tensorflow.lite as tflite
from tensorflow.keras.preprocessing import image
import tempfile




database_name = "Rail_madad"
passenger_collection = "user_passenger"
complaints_collection = "complaints"
pnr_collection = "pnr"
journey_collection = "journey"
train_manager_collection = "journey"
user_idgen = lambda: uuid4().hex[:12]


def home(request):
    return HttpResponse("WELCOME TO DJANGO SERVER WE ARE BUILDING AN APP FOR RAIL MADAD")


def connection():
    client = MongoClient(os.getenv("ATLAS"),server_api=ServerApi('1'))
    # client = MongoClient(os.getenv("HOST"))
    db = client.get_database(f'{database_name}')
    return db


@api_view(['POST'])
def register(request):
    db = connection()
    collection = db.get_collection(f'{passenger_collection}')
    if request.method == "POST":
        required_fields = ["username", "email", "password", "phonenumber"]

        # Check if all fields are present
        if not all(request.data.get(field) for field in required_fields):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        passenger_data = {
            "user_id": user_idgen(),
            "username": request.data.get('username'),
            "email": request.data.get("email"),
            "password": make_password(password=request.data.get("password"),hasher="default"),
            "phonenumber": str(request.data.get('phonenumber')),
            "complaint_raised": [], #shall have collection of raised complaints though out his life
            "pnr": None,
        }
        email = request.data.get('email')
        if not collection.find_one({"email": email}):
            collection.insert_one(passenger_data)
            register_email(email)

        else:
            return JsonResponse({"error": "account already exits"})
        db.client.close()
        return JsonResponse({"status": "registeration successfull!"},status= 201)


@api_view(['POST'])
def login(request):
    db = connection()
    collection = db.get_collection(passenger_collection)

    if request.method == "POST":
        usermail = request.data.get("email")
        password = request.data.get("password")

        temp = collection.find_one({"email": usermail}, {"_id": 0, "username": 1, "password": 1, "user_id": 1})

        if usermail == "admin@gmail.com" and password == "1234":
            db.client.close()
            return JsonResponse({"message": "dummy Login successful", "status": "success", "pass": password})

        elif temp:
            if check_password(password, temp.get("password")):
                user_id = temp.get("user_id")
                username = temp.get("username")

                #Create access and refresh tokens manually
                access_payload = {
                    'user_id': user_id,
                    'email': usermail,
                    'username': username,
                    'exp': datetime.now(timezone.utc) + timedelta(minutes=120),  # access token expires in 15 mins
                    'iat': datetime.now(timezone.utc)
                }
                access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')

                refresh_payload = {
                    'user_id': user_id,
                    'email': usermail,
                    'exp': datetime.now(timezone.utc) + timedelta(days=7),  # refresh token expires in 7 days
                    'iat': datetime.now(timezone.utc)
                }
                refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

                db.client.close()
                return JsonResponse({
                    "message": f"{username}'s Login successful",
                    "status": "success",
                    "user_id": user_id,
                    "access": access_token,
                    "refresh": refresh_token
                })
            else:
                return JsonResponse(
                    {"message": f"{temp.get('username')}'s Login failed", "status": "wrong credentials"})
        else:
            db.client.close()
            return JsonResponse({"message": "Invalid credentials", "status": "error"}, status=400)

    db.client.close()
    return JsonResponse({"error": "Invalid request method"}, status=405)


def verify(request):
    return HttpResponse("verify")

@api_view(['POST'])
def raise_complaint(request):

    decoded = decoder(request)
    user_email_from_token = decoded.get('email')
    user_id_from_token = decoded.get('user_id')

    try:
        pnr = request.data.get("pnr")
        complaint_type = request.data.get("complaint_type")
        complaint_description = request.data.get("complaint_description")

        if not all([pnr, complaint_type, complaint_description]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        db = connection()
        Passenger_collection = db.get_collection(passenger_collection)
        Pnr_collection = db.get_collection(pnr_collection)
        Complaint_collection = db.get_collection(complaints_collection)
        Journey_collection = db.get_collection(journey_collection)

        # Fetch user data using email from token
        user_data = Passenger_collection.find_one({"email": user_email_from_token})
        if not user_data:
            return JsonResponse({"error": "User not found"}, status=404)

        # Fetch PNR data
        pnr_data = Pnr_collection.find_one({"Pnr": pnr})
        if not pnr_data:
            return JsonResponse({"error": "PNR not found"}, status=404)

        train_number = str(pnr_data.get("TrainNo"))

        # Fetch train manager data
        current_train_manager_data = Journey_collection.find_one({"train_number": train_number})
        if not current_train_manager_data:
            return JsonResponse({"error": "Train manager not found"}, status=404)

        manager_name = current_train_manager_data.get("train_manager_name")
        manager_id = current_train_manager_data.get("manager_id")
        manager_number = current_train_manager_data.get("train_manager_number")

        # Create complaint
        complaint_data = {
            "complaint_id": user_idgen()[:6],
            "auto/manual": "manual",
            "train_number": train_number,
            "reported_by": {
                "username": user_data.get("username"),
                "user_id": user_data.get("user_id"),
                "pnr": pnr
            },
            "train_manager": {
                "name": manager_name,
                "manager_id": manager_id,
            },
            "complaint_type": complaint_type,
            "complaint_description": complaint_description,
            "status": "reported"
        }

        try:
            Complaint_collection.insert_one(complaint_data)
            Passenger_collection.update_one(
                {"email": user_email_from_token},
                {"$push": {
                    "complaint_raised": {
                        "complaint_id": complaint_data["complaint_id"],
                        "complaint_type": complaint_type,
                        "status": complaint_data['status'],
                        "manager_number": manager_number
                    }
                }}
            )
            Journey_collection.update_one(
                {"train_number": train_number},
                {"$push": {
                    "complaints": {
                        "complaint_id": complaint_data["complaint_id"],
                        "complaint_type": complaint_type,
                        "status": complaint_data['status']
                    }
                }}
            )

            raise_complaint_mail(user_email_from_token)
            db.client.close()
            return JsonResponse({"status": "Complaint raised successfully"}, status=201)

        except Exception as e:
            db.client.close()
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)

    except Exception as e:
        return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)




@api_view(['POST'])
def predict_complaint(request):
    decoded = decoder(request)
    user_email_from_token = decoded.get('email')
    user_id_from_token = decoded.get('user_id')

    model_path = os.path.join(settings.BASE_DIR, 'ml_model', 'model.tflite')

    if not user_id_from_token:
        return JsonResponse({'error': "no email from token found"}, status=400)

    # Load the class names
    class_names_path = os.path.join(settings.BASE_DIR, 'ml_model', 'class_names.txt')
    with open(class_names_path, "r") as f:
        class_names = [line.strip() for line in f.readlines()]

    # Load the TFLite model
    interpreter = tflite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Category Mapping
    CATEGORY_MAP = {
        "Security": ["fire smoke", "trackdefective"],
        "Medical": ["medical assist"],
        "Cleanliness": ["unclean_coach"],
        "Electrical": ["defective switch"],
        "General": ["overcrowding", "broken glass"],
        "Not a Complaint": ["tracknotdefective", "clean coach", "normal", "non defective switch"],
        "Coach Maintenance": ["torn bed"]
    }

    def general_output(predicted_class):
        predicted_class = predicted_class.lower()
        for category, class_list in CATEGORY_MAP.items():
            if predicted_class in class_list:
                return {"category": category, "subcategory": predicted_class}

    def predict_image(img_path):
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 127.5 - 1  # Preprocessing for MobileNet

        interpreter.set_tensor(input_details[0]['index'], img_array)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])

        predicted_class = np.argmax(output[0])
        confidence = output[0][predicted_class]
        return predicted_class, confidence

    # ✅ GET IMAGE FROM API
    if 'image' not in request.FILES:
        return JsonResponse({'error': "No image uploaded"}, status=400)

    uploaded_image = request.FILES['image']

    # Save uploaded image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        for chunk in uploaded_image.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name

    # Predict
    predicted_class, confidence = predict_image(temp_file_path)
    predicted_class_name = class_names[predicted_class]

    result = general_output(predicted_class_name)

    if not result:
        return JsonResponse({'error': "Could not classify the image properly"}, status=400)

    # You can now raise complaint automatically here if you want.
    # E.g., Create a complaint document in MongoDB using 'result'

    return JsonResponse({
        "user_id": user_id_from_token,
        "usermail": user_email_from_token,
        "predicted_category": result['category'],
        "predicted_subcategory": result['subcategory'],
        "confidence": float(confidence),
        "message": "Complaint auto-categorized successfully"
    }, status=200)


@api_view(['POST'])
#pnr #complaint_type = predicted complain #description = sub complaint .. (refer predict complaint)
def confirm_complaint(request):
    decoded = decoder(request)
    user_email_from_token = decoded.get('email')

    try:
        pnr = request.data.get("pnr")
        complaint_type = request.data.get("complaint_type")
        complaint_description = request.data.get("complaint_description")

        if not all([pnr, complaint_type, complaint_description]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        db = connection()
        Passenger_collection = db.get_collection(passenger_collection)
        Pnr_collection = db.get_collection(pnr_collection)
        Complaint_collection = db.get_collection(complaints_collection)
        Journey_collection = db.get_collection(journey_collection)

        # Fetch user data using email from token
        user_data = Passenger_collection.find_one({"email": user_email_from_token})
        if not user_data:
            return JsonResponse({"error": "User not found"}, status=404)

        # Fetch PNR data
        pnr_data = Pnr_collection.find_one({"Pnr": pnr})
        if not pnr_data:
            return JsonResponse({"error": "PNR not found"}, status=404)

        train_number = str(pnr_data.get("TrainNo"))

        # Fetch train manager data
        current_train_manager_data = Journey_collection.find_one({"train_number": train_number})
        if not current_train_manager_data:
            return JsonResponse({"error": "Train manager not found"}, status=404)

        manager_name = current_train_manager_data.get("train_manager_name")
        manager_id = current_train_manager_data.get("manager_id")
        manager_number = current_train_manager_data.get("train_manager_number")

        complaint_data = {
            "complaint_id": user_idgen()[:6],
            "auto/manual": "automatic",
            "train_number": train_number,
            "reported_by": {
                "username": user_data.get("username"),
                "user_id": user_data.get("user_id"),
                "pnr": pnr
            },
            "train_manager": {
                "name": manager_name,
                "manager_id": manager_id,
            },
            "complaint_type": complaint_type,
            "complaint_description": complaint_description,
            "status": "reported"
        }
        try:
            Complaint_collection.insert_one(complaint_data)
            Passenger_collection.update_one(
                {"email": user_email_from_token},
                {"$push": {
                    "complaint_raised": {
                        "complaint_id": complaint_data["complaint_id"],
                        "complaint_type": complaint_type,
                        "status": complaint_data['status'],
                        "manager_number": manager_number
                    }
                }}
            )
            Journey_collection.update_one(
                {"train_number": train_number},
                {"$push": {
                    "complaints": {
                        "complaint_id": complaint_data["complaint_id"],
                        "complaint_type": complaint_type,
                        "status": complaint_data['status']
                    }
                }}
            )

            raise_complaint_mail(user_email_from_token)
            db.client.close()
            return JsonResponse({"status": "Complaint raised successfully"}, status=201)

        except Exception as e:
            db.client.close()
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)

    except Exception as e:
        return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
