import time
import tango

if __name__ == "__main__":
    # test tango attribute read speed
    device_name = "et7000_server/test/pet15_7018"
    attr_name = "IP"

    dp = tango.DeviceProxy(device_name)

    # timing benchmarks
    print('Timing benchmarks')

    from matplotlib import pyplot as plt
    import numpy as np

    N = 5000
    y = np.zeros(N)
    z = []
    n = 1
    t = 0.0
    n1 = 1
    t1 = 0.0
    tmin = 1e60
    tmax = -1.0
    error_unt = 0
    error_t = 0.0
    error_count = 0

    for i in range(N):
        t0 = time.perf_counter()
        a = dp.read_attribute(attr_name)
        dt = (time.perf_counter() - t0) * 1000.0
        v = a.value
        if a is None:
            error_count += 1
            error_t += dt
        y[i] = dt
        z.append(v)
        t += dt
        n += 1
        ar = t / n
        t1 += dt
        n1 += 1
        ar1 = t1 / n1
        tmin = min(tmin, dt)
        tmax = max(tmax, dt)
        #print(f'\rRead: {attr_name} {a} {dt} {tmin} {tmax}', end='')
        if t1 > 5000.0:
            t1 = 0.0
            n1 = 0.0
    if error_count > 0:
        error_avg_dt = error_t / error_count
        print('\n Total errors: %s avg_dt=%s ms' % (error_count, error_avg_dt))
    else:
        print('\n No errors!')

    print(f'\rRead: {attr_name} tmin: {tmin} tmax: {tmax} avg: {ar}')

    # plot data
    #x = np.arange(N)
    #fig, ax = plt.subplots()
    #ax.plot(x, y)
    #ax.set(xlabel='N', ylabel='time (ms)',
    #       title='Read timings')
    #ax.grid()
    ## fig.savefig("test.png")
    #plt.show()

    # the histogram of the data
    num_bins = 500
    fig, ax = plt.subplots()
    n, bins, patches = ax.hist(y, num_bins, density=True)
    ax.set_xlabel('time (ms)')
    ax.set_ylabel('Probability density')
    ax.set_title(r'Histogram of Read timing')
    # ax.set_title(r'Histogram of Read timing: $\mu=100$, $\sigma=15$')
    # Tweak spacing to prevent clipping of ylabel
    fig.tight_layout()
    plt.show()
