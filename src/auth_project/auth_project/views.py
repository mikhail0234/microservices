from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, JsonResponse
from oauth2_provider.decorators import protected_resource


@login_required()
def secret_page(request, *args, **kwargs):
    return HttpResponse('OK', status=200)

@login_required()
def get_user(request, *args, **kwargs):
    user = request.user
    return JsonResponse({"id":user.pk}, status=200, content_type='application/json')