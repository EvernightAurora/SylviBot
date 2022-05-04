

def detect_order(msg:str, order0, argrange=0):
    if type(argrange) is int:
        argrange = [argrange]
    if argrange == [0]:
        return (msg == order0), None
    if 0 in argrange and msg.lower() == order0:
        return True, []
    if type(argrange) is int:
        argrange = [argrange]
    if type(argrange) is not list:
        argrange = list(argrange)
    order = order0 + ' '
    if msg[:len(order)].lower() != order:
        return False, None
    last = msg[len(order):].strip().split()
    if len(last) in argrange:
        return True, last
    return False, last
