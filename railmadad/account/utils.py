import jwt
from django.conf import settings
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from django.http import JsonResponse

def decode_jwt_token(token):
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return decoded
    except ExpiredSignatureError:
        return {'error': 'Token has expired'}
    except InvalidTokenError:
        return {'error': 'Invalid token'}

def decoder(request):
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return JsonResponse({'error': 'Authorization header missing'}, status=401)
    try:
        bearer, token = auth_header.split(' ')
        if bearer != 'Bearer':
            return JsonResponse({'error': 'Invalid token header'}, status=401)
    except ValueError:
        return JsonResponse({'error': 'Invalid Authorization header format'}, status=401)
    decoded = decode_jwt_token(token)
    if 'error' in decoded:
        return JsonResponse({'error': decoded['error']}, status=401)
    else:
        return decoded

