def hard_sleep(request):

    a = 0
    for i in range(3000):
        for j in range(10000):
            a += i * j

    return {
        'msg': 'Hard Sleep'
    }
