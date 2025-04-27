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
        return ({'error': 'Authorization header missing'})
    try:
        bearer, token = auth_header.split(' ')
        if bearer != 'Bearer':
            return ({'error': 'Invalid token header'})
    except ValueError:
        return ({'error': 'Invalid Authorization header format'})
    decoded = decode_jwt_token(token)
    if 'error' in decoded:
        return ({'error': decoded['error']})
    else:
        return decoded

