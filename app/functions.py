import time


def measure(filename, start, power, tcs, state='??'):
    t = time.time()
    V = power.get_V().strip('V')
    I = power.get_I().strip('A')
    temperatures = '\t'.join(list(map(str, tcs.get_T())))

    output = "%f\t%s\t%s\t" % (t - start, I, V) + temperatures + '\t%s' %state
    with open(filename, 'a') as file:
        file.write(output + "\n")
