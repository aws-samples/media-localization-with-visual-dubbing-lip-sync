from subprocess import CalledProcessError

from retrying import retry
from sagemaker_inference import model_server
import handler_service

HANDLER_SERVICE = handler_service.__file__

def _retry_if_error(exception):
    return isinstance(exception, CalledProcessError)

@retry(stop_max_delay=1000 * 30,
       retry_on_exception=_retry_if_error)
def _start_model_server():
    model_server.start_model_server(handler_service=HANDLER_SERVICE)
    
if __name__ == '__main__':
    _start_model_server()