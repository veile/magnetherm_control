import time
import app.utils as utils

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


def time_exp(power, temp, current, filename, rec_before, N, on_time, off_time, rec_after, dt):
    state = 'BEFORE'
    n = 0  # iterator that stops when it reaches N

    # Initially sets the time to a number divisible by the sample rate
    time.sleep(dt - (time.time() % dt))
    start = time.time()
    while (time.time() - start) < (rec_before + N * (on_time + off_time) + rec_after):
        exposing = utils.read_states()[0]
        if not exposing:
            return "Experiment stopped"

        measure(filename, start, power, temp, state=state)
        temp.initiate()

        if (time.time() - start) > rec_before - 0.1 and state == 'BEFORE':
            state = 'EXPOSING'
            power.set(V=45, I=current)
            power.set_output('ON')

        if (time.time() - start) > (rec_before + (
                n + 1) * on_time + n * off_time - 0.1) and state == 'EXPOSING':  # 0.1 s to account for small drifts
            n += 1

            # Changing state
            state = 'WAIT'

            # Sets output to 0V and 0A and output to off
            power.set_default()

        if (time.time() - start) > (rec_before + n * (on_time + off_time) - 0.1) and state == 'WAIT':
            state = 'EXPOSING'
            power.set(V=45, I=current)
            power.set_output('ON')

        if (time.time() - start) > (rec_before + N * (on_time + off_time) - 0.1) and state == 'EXPOSING':
            # Changing state
            state = 'WAIT'

            # Sets output to 0V and 0A and output to off
            power.set_default()

        time.sleep(dt - (time.time() % dt))

    return 'Exposure done'

def temp_exp(power, temp, current, filename, rec_before, N, Tset, Trange, rec_after, dt):
    state = 'BEFORE'

    n = 0  # iterator that stops when it reaches N

    # Initially sets the time to a number divisible by the sample rate
    time.sleep(dt - (time.time() % dt))
    start = time.time()
    while n < N:
        exposing = utils.read_states()[0]
        if not exposing:
            return "Experiment stopped"

        measure(filename, start, power, temp, state=state)
        # Read latest temperature
        with open(filename, 'r') as f:
            last_line = f.read().splitlines()[-1]
            Tlast = float(last_line.split('\t')[-2])

        # Initiate next temperature measurements
        temp.initiate()

        if (time.time() - start) > rec_before - 0.1 and state == 'BEFORE':
            state = 'EXPOSING'
            power.set(V=45, I=current)
            power.set_output('ON')

        if Tlast>(Tset+Trange) and state == 'EXPOSING':  # 0.1 s to account for small drifts
            n += 1

            # Changing state
            state = 'WAIT'

            # Sets output to 0V and 0A and output to off
            power.set_default()

        if Tlast < (Tset - Trange) and state == 'WAIT':
            state = 'EXPOSING'
            power.set(V=45, I=current)
            power.set_output('ON')

        time.sleep(dt - (time.time() % dt))

    time.sleep(dt - (time.time() % dt))
    after_timer = time.time()
    while (time.time()-after_timer) < rec_after:
        exposing = utils.read_states()[0]
        if not exposing:
            return "Experiment stopped"

        measure(filename, start, power, temp, state=state)
        # Initiate next temperature measurements
        temp.initiate()
        time.sleep(dt - (time.time() % dt))

    return 'Exposure done'