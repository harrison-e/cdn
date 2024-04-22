# httpserver.py - contains HTTPServer, for use in httpserver script

# +-----------+
# |  Imports  |
# +-----------+
import socket, sys, requests, urllib 
from requests import HTTPError
from .cache import Cache

# +-------------+
# |  Constants  |
# +-------------+
MAX_CACHE_SIZE = 20 * 1000 * 1000 # bytes

ANYWHERE    = '0.0.0.0'
LOCALHOST   = '127.0.0.1'
HTTP_VER    = 'HTTP/1.1'
HTTP_CRLF   = '\r\n'
BEACON_PATH = '/grading/beacon'

ORIGIN_REQ_HEADERS  = {
        'User-Agent': 'Harrison\'s Super Awesome HTTP Server',
        'Accept': 'text/html',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
        }
CLIENT_RESP_HEADERS = {
        'Server': 'Harrison\'s Super Awesome HTTP Server',
        'Content-Type': 'text/html',
        'Connection': 'close'
        } 



# +---------------+
# |  HTTP Server  |
# +---------------+
class HTTPServer:
    # -- Constructor --
    # > Creates a HTTP Server with specified arguments
    def __init__(self, args):
        self.port = args.port
        self.origin = args.origin
        self.verbose = args.verbose

        # Hack to close any sockets left open
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.close()

        # Listen for clients on a different socket, bound to anywhere (0.0.0.0),
        #   on this server's port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.bind((ANYWHERE, self.port))
        self.client_socket.listen()

        # Create a cache with MAX_CACHE_SIZE, that requests files 
        self.cache = Cache(max_size=MAX_CACHE_SIZE,
                           request_function=self.origin_request_file,
                           refresh_rate=25,
                           verbose=self.verbose)


    # -- Log --
    # > Prints a message if the server is in verbose mode
    def log(self, message):
        if self.verbose:
            sys.stderr.write('Log: ' + message + '\n')


    # -- Parse Client Request Filepath --
    # > Parses raw data from a socket into a filepath 
    # ! May raise a HTTPError if the request is not valid 
    def parse_client_request_filepath(self, request_raw):
        self.log(f'Received client request:\n{request_raw}')

        # Split text into request line and headers, validate 
        try:
            request_line, headers = request_raw.split('\r\n', 1)
            method, url, protocol = request_line.split(' ', 3)
        except ValueError:
            raise HTTPError('Could not parse request line from headers')

        # We only take GETs here!
        if method != 'GET':
            raise HTTPError('This server only takes GET requests')

        # If request is valid HTTP, parse/validate path 
        try: 
            parsed_url = urllib.parse.urlparse(url)
        except ValueError:
            raise HTTPError('Invalid URL')

        # All clear, return path
        return parsed_url.path


    # -- Send Client Response --
    # > Constructs a response to send to a given connection,
    #   with given status code, reason, and payload
    # > Response headers are defined above in Constants, as 
    #   CLIENT_RESP_HEADERS
    # > Assumes that client accepts 'text/html'
    # > Since we are always closing our connection, do not 
    #   need to include 'Content-Length' header 
    def send_client_response(self, conn, status_code, reason, payload=None):
        # Construct HTTP response
        response = HTTP_VER + f' {status_code} ' + reason + HTTP_CRLF
        for header_name in CLIENT_RESP_HEADERS:
            response += header_name + ': ' + CLIENT_RESP_HEADERS[header_name] + HTTP_CRLF 
        response += HTTP_CRLF   # extra \r\n signals end of headers

        # Finally, send fully constructed response
        response_data = bytearray(response, 'utf-8')
        response_data += payload
        conn.sendall(bytes(response_data))


    # -- Request File --
    # > Sends a GET request for 'filepath' to the origin server 
    # > Returns raw data from the server
    # ! May raise a FileNotFoundError if the path is not on 
    #   the server
    def origin_request_file(self, filepath):
        # Construct a request, prepare, and send to origin
        with requests.Session() as s:
            origin_request = requests.Request(method = 'GET',
                                              url = (self.origin + ':8080' + filepath),
                                              headers = ORIGIN_REQ_HEADERS)
            origin_request = origin_request.prepare()

            self.log(f'Sending request to {self.origin} for {filepath}')
            try:
                origin_response = s.send(origin_request)
            except Exception:
                raise FileNotFoundError(f'Server failed to fetch {filepath}')
            
            # Make sure that response is 200 OK
            if origin_response.status_code != 200:
                raise FileNotFoundError(f'Origin server returned {origin_response.status_code}')
            
            # Return content from origin response 
            return origin_response.content


    # -- Start --
    # > Starts the HTTP Server, which continuously accepts clients 
    def start(self):
        # Check that we have a client socket 
        if not self.client_socket:
            self.log('HTTP server could not connect to client')
            sys.exit(1)

        # Listen forever!
        while True:
            conn, addr = self.client_socket.accept()
            with conn:
                self.log(f'HTTP server connected to from {addr}')

                # Receive HTTP request from client
                client_request_raw = ''
                while True:
                    data = conn.recv(1024)
                    client_request_raw += data.decode('ascii') 
                    # \r\n\r\n indicates that headers of a request 
                    #   are complete, and we don't care about
                    #   the request body (in this application!)
                    if (HTTP_CRLF + HTTP_CRLF) in client_request_raw:
                        break

                # Retrieve filepath from request, send error if invalid 
                try:
                    filepath = self.parse_client_request_filepath(client_request_raw)
                except HTTPError:
                    self.send_client_response(conn=conn, 
                                              status_code=400, 
                                              reason=f'Bad Request')
                    continue

                # Catch BEACON_PATH
                if filepath == BEACON_PATH:
                    self.send_client_response(conn=conn,
                                              status_code=204,
                                              reason='No Content')
                    continue
                
                # For all other paths:
                else:
                    # Pass all of our data retrieval through the Cache,
                    #   to keep all of that sweet, sweet metadata
                    try:
                        data = self.cache.get(filepath)
                    except FileNotFoundError:
                        self.send_client_response(conn=conn,
                                                  status_code=404,
                                                  reason=f'Not Found')
                        continue

                    # If we can get the requested file, send to client 
                    self.send_client_response(conn=conn,
                                              status_code=200,
                                              reason='OK',
                                              payload=data)
