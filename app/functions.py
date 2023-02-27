import time


def measure(filename, start, power, tcs, state='??'):
    t = time.time()

    try:
        V = power.get_V().strip('V')
        I = power.get_I().strip('A')
        temperatures = '\t'.join(list(map(str, tcs.get_T())))

        output = "%f\t%s\t%s\t" %(t - start, I, V) + temperatures + '\t%s' %state

    except ValueError as e:
        # Valueerror is often caused by checksum error in the temperature probe - flushing the temperature probe
        tcs.reinitialize()
        
        output = "%f\t-1\t-1\t" %(t - start) + '\t'.join(list(map(str, [-274]*len(tcs)))) + '\tERROR'
        with open(filename[:-4]+'.log', 'a') as file:
            file.write("%f\t" %(t - start) + str(e) + "\n")    

    except Exception as e:
        output = "%f\t-1\t-1\t" %(t - start) + '\t'.join(list(map(str, [-274]*len(tcs)))) + '\tERROR'
        with open(filename[:-4]+'.log', 'a') as file:
            file.write("%f\t" %(t - start) + str(e) + "\n")

    with open(filename, 'a') as file:
        file.write(output + "\n")
