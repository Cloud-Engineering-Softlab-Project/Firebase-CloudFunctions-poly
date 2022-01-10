def soft_sleep(request):

    a = 0
    for i in range(1000):
        for j in range(10000):
            a += i * j

    return {
        'msg': 'Soft Sleep'
    }
