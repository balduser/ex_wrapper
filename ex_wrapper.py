from Exscript import Account
from Exscript.protocols import SSH2
# To be done: description, execute_file
class Commutator:
    """Creates objects that may be interacted like commutators
    Method performed with a commutator (commutator-methods) are:
        execute_file()
        show_int()
        show_run()
        show_sw()
        version()
    Methods performed with port (port-methods) are:
        get_poe(port, **kwargs)
        get_vlan(port, **kwargs)
        link_state(port)
        set_poe(port, **kwargs)
        set_vlan(port, **kwargs)
        show_int(port)
        show_run(port)
    Port-methods always get the port number as a first argument (see parse_portnumber() docstring)."""

    default_login = 'admin'
    default_password = 'admin'

    def __init__(self, ip, login=default_login, password=default_password, **kwargs):
        """kwargs are:
        brand: str - 'Eltex', 'Cisco', etc.
        model: str - 'MES 2324', etc."""

        self.ip = ip
        self.__login = login
        self.__password = password
        self.brand = kwargs['brand'] if 'brand' in kwargs else 'Eltex'
        self.model = kwargs['model'] if 'model' in kwargs else None
        acc = Account(self.__login, self.__password)
        print('Connecting to ', ip)
        self.__conn = SSH2()
        self.__conn.connect(ip)
        self.__conn.login(acc)
        self.__conn.execute('terminal datadump')
        print('Logged in')


    def __repr__(self):
        return f'{self.brand} commutator, ip {self.ip}'


    def parse_portnumber(self, *args):
        """Parsing port from the first position argument
        as int:
            1 for GigabitEthernet 1/0/1,
            24 for GigabitEthernet 1/0/24,
            222 for GigabitEthernet 2/0/22,
            1001 for TengigabitEthernet 1/0/1,
            1404 for TengigabitEthernet 4/0/4 etc
        as list:
            ['gi',1,0,1] for GigabitEthernet 1/0/1,
        as string:
            "po 1" for port-channel 1
            "whatever" for whatever"""

        interface = args[0]
        if isinstance(interface, int):
                if interface < 100:
                    return f'gi 1/0/{interface}'
                elif 100 < interface < 1000:
                    return f'gi {interface // 100}/0/{interface % 100}'
                elif 1000 < interface < 1100:
                    return f'te 1/0/{interface%100}'
                else:
                    return f'te {(interface-1000) // 100}/0/{interface % 100}'
        elif isinstance(interface, list):
                return f'{interface[0]} {interface[1]}/{interface[2]}/{interface[3]}'
        elif isinstance(interface, str):
                return interface


    def show_int(self, *args):
        """With no arguments returns result of `show interfaces` command
        To get the result `show interfaces <>` it takes the port number argument
        Returns a string"""

        if args:
            interface = self.parse_portnumber(*args)
            command = f'sh int {interface}'
        else:
            command = 'sh int'
        self.__conn.execute(command)
        answer = self.__conn.response
        return answer


    def show_run(self, *args):
        """With no arguments returns result of `show running-config` command
        To get the result `show running-config interface <>` it takes the port number argument
        Returns a string"""

        if args:
            interface = self.parse_portnumber(*args)
            command = f'sh ru int {interface}'
        else:
            command = 'sh ru'
        self.__conn.execute(command)
        answer = self.__conn.response
        return answer


    def show_sw(self):

        try:
            self.__conn.execute('show version')
            answer = self.__conn.response
            for line in answer.split('\n'):
                if 'Version' in line:
                    return line.split('Version:')[1].strip()
        except:
            pass

    def link_state(self, *args):
            """Returns 1 is port's link state is up and 0 if it's down"""

        try:
            interface = self.parse_portnumber(*args)
            self.__conn.execute(f'show int status {interface}')
            answer = self.__conn.response.split('\n')
            for i, line in enumerate(answer):
                if 'Port' in line:
                    ans = answer[i+2].split()[6]
                    if ans == 'Up':
                        return True
                    elif ans == 'Down':
                        return False
        except:
            pass


    def get_vlan(self, *args, **kwargs):
        """Returns information about vlans setup. Cannot be launched without arguments, selecting an interface is necessary.
        Parameters for selecting are the same as in show_run(). Returns a dict e.g.:
            {'mode': 'trunk', 'allowed': 104, 'native': 110, 'mtv': 118}
            {'mode': 'access', 'access': 107}
        With a parameter mode='list' returns a list of strings, e.g.:
            ['switchport mode trunk', 'switchport trunk allowed vlan add 104', 'switchport trunk native vlan 110']
        With a parameter mode='mode' returns a string:
            'access' | 'trunk' | 'customer' | 'general' """

        answer = self.show_run(*args)
        if 'mode' in kwargs:
            if kwargs['mode'] == 'mode':
                for line in answer.split('\n'):
                    if 'switchport access' in line:
                        return 'access'
                    elif 'switchport mode trunk' in line:
                        return 'trunk'
                    elif 'switchport mode customer' in line:
                        return 'customer'
                    elif 'switchport mode general' in line:
                        return 'general'
            elif kwargs['mode'] == 'list':
                return [line.strip() for line in answer.split('\n') if 'switchport' in line]
        else:
            d = {}
            for line in answer.split('\n'):
                if 'switchport access vlan' in line:
                    d['mode'] = 'access'
                    d['access'] = int(line.strip().split(' ')[-1])
                elif 'multicast-tv vlan' in line:
                    d['mtv'] = int(line.strip().split(' ')[-1])
                elif 'switchport mode trunk' in line:
                    d['mode'] = 'trunk'
                elif 'switchport trunk native' in line:
                    d['native'] = int(line.strip().split(' ')[-1])
                elif 'switchport trunk allowed' in line:
                    d['allowed'] = (line.strip().split(' ')[-1])
            return d


    def set_vlan(self, *args, **kwargs):
        """Setting a switchport configuration.
        Number of port is given like in show_run().
        Configuration must be given in a dict, e.g.:
            {'mode': 'trunk', 'allowed': '102,104,111-112', 'native': 110}
            {'mode': 'access', 'access': 107, 'mtv': 118}
        Empty dict {} means removing all switchport records"""

        interface = self.parse_portnumber(*args)
        for arg in args:
            if isinstance(arg, dict):
                current_setup = self.get_vlan(*args, **kwargs)
                print('current: ', current_setup)
                print('Dict to be set: ', arg)
                # this arg must be a dict with parameters to be implemented
                self.__conn.execute('config')
                self.__conn.execute(f'interface {interface}')

                # First we clear the config
                if current_setup and current_setup['mode'] == 'trunk':
                    self.__conn.execute(f"no switchport trunk multicast-tv vlan")
                    print('2', self.__conn.response)
                    self.__conn.execute(f"switchport trunk allowed vlan remove all")
                    print('3', self.__conn.response)
                    self.__conn.execute(f"no switchport trunk native vlan")
                    print('1', self.__conn.response)
                if current_setup and current_setup['mode'] == 'access':
                    self.__conn.execute(f"no switchport access multicast-tv vlan")
                    print('4', self.__conn.response)
                    self.__conn.execute('no switchport access vlan')
                    print('4+', self.__conn.response)
                self.__conn.execute(f"no switchport mode")
                print('0', self.__conn.response)

                # Then we set it up
                if not arg:
                    # If the dict is empty, there's no need to set switchport
                    self.__conn.execute('ex')
                    self.__conn.execute('ex')
                    return None
                print(f"switchport mode {arg['mode']}")
                self.__conn.execute(f"switchport mode {arg['mode']}")
                print('5', self.__conn.response)
                if arg['mode'] == 'trunk':
                    if 'allowed' in arg:
                        self.__conn.execute(f"switchport trunk allowed vlan add {arg['allowed']}")
                        print('6', self.__conn.response)
                    if 'native' in arg:
                        self.__conn.execute(f"switchport trunk native vlan {arg['native']}")
                        print('7', self.__conn.response)
                    if 'mtv' in arg:
                        self.__conn.execute(f"switchport trunk multicast-tv vlan {arg['mtv']}")
                        print('8', self.__conn.response)
                elif arg['mode'] == 'access':
                    self.__conn.execute(f"switchport access vlan {arg['vlan']}")
                    print('9', self.__conn.response)
                    if 'mtv' in arg:
                        self.__conn.execute(f"switchport access multicast-tv vlan {arg['mtv']}")
                        print('10', self.__conn.response)

                # Exiting
                self.__conn.execute('ex')
                self.__conn.execute('ex')


    def execute_file(self, filename):
        """Reading a file and consequent executing each instruction to the commutator configuration"""
        pass


    def get_poe(self, *args, **kwargs):
        """Getting information about POE on a port.
        returns True is operational Poe status is on
        returns False is operational Poe status is off or fault
        if mode='current', returns float (mA)
        if mode='voltage', returns float (Volts)
        if mode='verbose', returns detailed info about the port
        in case of trouble returns None"""

        interface = self.parse_portnumber(*args)
        # Somewhy Exscript throws InvalidCommandException after requesting Poe. But output is ok
        try:
            command = f'show power inline {interface}'
            self.__conn.execute(command)
        except:
            try:
                answer = self.__conn.response.lstrip(command + '\n')
            except:
                pass
        try:
            if 'mode' in kwargs:
                if kwargs['mode'] == 'verbose':
                    return answer
                if kwargs['mode'] == 'current':
                    for line in answer.split('\n'):
                        if 'Current' in line:
                            return float(line.strip().split(' ')[-1])
                elif kwargs['mode'] == 'voltage':
                    for line in answer.split('\n'):
                        if 'Voltage' in line:
                            return float(line.strip().split(' ')[-1])
            else:
                for line in answer.split('\n'):
                    if 'Port Status' in line:
                        if 'Port is on' in line:
                            return True
                        else:
                            return False
        except:
            pass


    def set_poe(self, *args, **kwargs):
        """Setting POE operational status on a port
        Gets a portnumber and True/False. For True sets power inline to 'auto', for False - to 'never'
        After the succesfull execution returns True, in case of trouble returns None"""

        interface = self.parse_portnumber(*args)
        try:
            self.__conn.execute('config')
            self.__conn.execute(f'interface {interface}')
            if True in args:
                self.__conn.execute(f'power inline auto')
            elif False in args:
                self.__conn.execute(f'power inline never')
            self.__conn.execute('ex')
            self.__conn.execute('ex')
            return True
        except:
            pass


    def __del__(self):
        print('Disconnecting')
        try:
            self.__conn.send('exit\r')
            self.__conn.close()
        except:
            print('Error while disconnecting from the device')
