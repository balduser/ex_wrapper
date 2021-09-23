from ex_wrapper import Commutator
from subprocess import Popen, PIPE
import sys


def pinger(ip):
    """Pinging the host by it's ip"""

    job = Popen(f"ping {ip} -n 100", stdout=PIPE, shell=True)
    while True:
        line = job.stdout.readline().decode('cp866')
        if line:
            yield line
        else:
            break


def check_reloading(ip):
    c_ping = iter(pinger(ip))
    device_available = True  # 0 - Working, 1 - Unavailable, 2 - Available again
    count_pings = 0  # Counting the lost pings to ensure that it was not a single packet loss
    try:  # try for KeyboardInterrupt
        while True:
            try:  # try for StopIteration
                answer = next(c_ping)
                print(answer)
                if device_available:
                    if c.ip not in answer:
                        count_pings += 1
                        if count_pings > 5:
                            device_available = False
                            print('Device is unavailable!')
                            count_pings = 0
                else:
                    if c.ip in answer:
                        count_pings += 1
                        if count_pings > 5:
                            print('Device is available again!')
                            # device_available = True
                            return True
            except StopIteration:
                break
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    c = Commutator('192.168.111.57', sys.argv[1], sys.argv[1], model='test MES2324')
    c51 = Commutator('192.168.20.51', 'admin', sys.argv[2])

    # Testing .version()
    assert c.version() == '4.0.13.3'
    print('\nVersion() - OK\n')

    # Testing .get_poe()
    for i in range(1, 25):
        ans = c51.get_poe(i, params=True)
        if ans['status']:
            print(f"Port{i}, {ans['power']} Watts, {ans['current']} mA, {ans['voltage']} Volts")
    print("\nGet_poe() - OK")

    Commutator.console_print = True

    # Testing .execute()
    assert "TEMPERATURE is OK" in c.execute("show environment temperature status")
    print('\nExecute() - OK\n')

    # Testing .link_state()
    # Links at ports gi0/1 and te0/1 must be Up and Down
    assert c.link_state(1)
    assert not c.link_state(('gi', 1, 0, 12))
    assert not c.link_state(1001)
    print('\nlink_state() - OK\n')

    # Testing .set_vlan


    # Testing execute_file() with lines "conf \ int gi0/2 \ no sw mo \ ex \ int gi0/12 \ sw mo ac \ sw ac vl 110 \
    # \ int gi0/24 \ sw mo ac \ sw ac vl 111 \ ex \ ex \ wr \ sh run int gi0/9 \ reload "
    '''assert c.execute_file('commands.txt')
    assert check_reloading(c.ip)
    print('\nExecute_file() with reloading - OK\n')'''
