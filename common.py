import httplib
import ssl
# connect restful API
def get_api(method, path, params, header, hostname, port):
    # print hostname
    conn = httplib.HTTPSConnection(hostname, int(port), context=ssl._create_unverified_context())
    conn.request(method, path, params, header)
    resp = conn.getresponse()
    return resp


if __name__ == '__main__':
    pass
