import logging
from scout_apm.core.tracked_request import TrackedRequest
from scout_apm.api.context import Context

# Logging
logger = logging.getLogger(__name__)


class MiddlewareTimingMiddleware:
    """
    Insert as early into the Middleware stack as possible (outermost layers),
    so that other middlewares called after can be timed.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with TrackedRequest.instance().span(operation='Middleware'):
            response = self.get_response(request)
            return response

class ViewTimingMiddleware:
    """
    Insert as deep into the middleware stack as possible, ideally wrapping no
    other middleware. Designed to time the View itself
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Wrap a single incoming request with start and stop calls.
        This will start timing, but relies on the process_view callback to
        capture more details about what view was really called, and other
        similar info.

        If process_view isn't called, then the request will not
        be recorded.  This can happen if a middleware further along the stack
        doesn't call onward, and instead returns a response directly.
        """

        tr = TrackedRequest.instance()

        # This operation name won't be recorded unless changed later in
        # process_view
        with tr.span(operation='Unknown'):
            response = self.get_response(request)
            return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Capture details about the view_func that is about to execute

        Does not start its own span, but saves onto the one started in the
        __call__ method of this middleware
        """

        tr = TrackedRequest.instance()
        tr.mark_real_request()
        span = tr.current_span()
        if span is not None:
            view_name = request.resolver_match._func_path
            span.operation = 'Controller/' + view_name
            Context.add('path', request.path)
            Context.add('user_ip', request.get_host())
            if request.user is not None:
                Context.add('username', request.user.username)

    def process_exception(self, request, exception):
        """
        Mark this request as having errored out

        Does not modify or catch or otherwise change the exception thrown
        """
        TrackedRequest.instance().tag('error', 'true')

    #  def process_template_response(self, request, response):
    #      """
    #      """
    #      pass
