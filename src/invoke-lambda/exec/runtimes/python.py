import importlib, json, os, traceback
from urllib.request import urlopen, Request

config = json.loads(os.environ.get('__ARC_CONFIG__'))
context = json.loads(os.environ.get('__ARC_CONTEXT__'))
runtime_api = os.environ.get('AWS_LAMBDA_RUNTIME_API')
del os.environ['__ARC_CONFIG__']
del os.environ['__ARC_CONTEXT__']

url = lambda p : runtime_api + '/2018-06-01/runtime/' + p
headers = { 'content-type': 'application/json' }

try:
  next = url('invocation/next')
  request = Request(next, data=None, headers={})
  invocation = urlopen(request)
  event = json.loads(invocation.read())

  requestID = invocation.getheader('Lambda-Runtime-Aws-Request-Id') or invocation.getheader('lambda-runtime-aws-request-id')
  errorEndpoint = url('invocation/' + requestID + '/error')
  responseEndpoint = url('invocation/' + requestID + '/response')

  try:
    # Python does funky stuff with importing absolute paths, hardcoding for now
    index = importlib.import_module('index')
    handler = getattr(index, 'handler')
    result = handler(event, context)
    data = json.dumps(result).encode('utf-8')
    request = Request(responseEndpoint, data=data, headers=headers)
    urlopen(request)

  except Exception as handler_err:
    print(traceback.format_exc())
    errorType = getattr(handler_err, 'message', repr(handler_err))
    stackTrace = traceback.format_exc()
    data = json.dumps({ 'errorType': errorType, 'stackTrace': stackTrace }).encode('utf-8')
    request = Request(errorEndpoint, data=data, headers=headers)
    urlopen(request)

except Exception as init_err:
  print(traceback.format_exc())
  initErrorEndpoint = url('init/error')
  errorType = getattr(init_err, 'message', repr(init_err))
  stackTrace = traceback.format_exc()
  data = json.dumps({ 'errorType': errorType, 'stackTrace': stackTrace }).encode('utf-8')
  request = Request(initErrorEndpoint, data=data, headers=headers)
  urlopen(request)
