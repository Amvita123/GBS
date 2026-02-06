from django_user_agents.middleware import UserAgentMiddleware


class SelectiveUserAgentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.user_agent_middleware = UserAgentMiddleware(get_response)

    def __call__(self, request):
        if 'sign-in' in request.path:
            return self.user_agent_middleware(request)
        return self.get_response(request)
