from bottle import run, post, get, request as bottle_request


@post('/')
@get('/')
def main():
    data = bottle_request.json  # <--- extract all request data
    print(data)
    return

if __name__ == '__main__':
    run(host='localhost', port=5001, debug=True)
