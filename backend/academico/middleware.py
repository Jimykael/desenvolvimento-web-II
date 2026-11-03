class CorsDevMiddleware:
    """CORS simples para desenvolvimento: permite abrir o frontend fora do Django
    (ex.: Live Server na porta 5500). A API usa token no header, sem cookies."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'OPTIONS' and request.path.startswith('/api/'):
            from django.http import HttpResponse
            resposta = HttpResponse(status=204)
        else:
            resposta = self.get_response(request)
        if request.path.startswith('/api/'):
            resposta['Access-Control-Allow-Origin'] = '*'
            resposta['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            resposta['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        return resposta
