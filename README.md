# ex_wrapper
Library-wrapper to simplify interaction with Eltex commutators. Creates objects that may be interacted like managed switches.

### Dependencies 
Requires ExScript:  
`pip install ExScript`

### Methods
Methods applied to a commutator (switch-methods) are:  
- `execute(command: str)` # Execute an arbitrary command. When executed, returns the output.  
- `execute_file(filename: str)` # Execute a script in a file. When executed, returns True.  
- `show_int()` # Returns the result of `show interfaces` command (string).  
- `show_run()` # Returns the result of `show running-config` command (string).  
- `version()` # Returns the version of firmware (string).  
- `write()` # Execute the `write` command. When executed, returns True.  

Methods applied to a port (port-methods) are:  
- `description(port, [description: str])` # Returns the desription (string) if no string if given. Sets if given.  
If the description string is empty, erases the description.
- `get_poe(port, **kwargs)` # Returns Poe parameters (see docstring).  
- `get_vlan(port, **kwargs)` # Returns information about vlan configuration (see docstring).  
- `link_state(port)` # Returns 1/0 for link state Up/Down.  
- `set_poe(port, status)` # Setting up Poe. For True sets `power inline` to 'auto', for False - to 'never'.  
- `set_vlan(port, **kwargs)` # Setting up vlan configuration.  
- `show_int(port)` # Returns the result of `show interfaces <port>`.  
- `show_run(port)` # Returns the result of `show running-config <port>`.  

Port-methods always get the port number as a first argument. It may be given:  
as int < 1000 - twisted pair ports:  
- `1` for GigabitEthernet 1/0/1,  
- `24` for GigabitEthernet 1/0/24,  
- `222` for GigabitEthernet 2/0/22,  
as int > 1000 - fiber optics ports:  
- `1001` for TengigabitEthernet 1/0/1,  
- `1404` for TengigabitEthernet 4/0/4  
as list or tuple:  
- `['fa', 1, 0, 1]` for FastEthernet 1/0/1,  
- `('te', 4, 0, 4)` for TengigabitEthernet 4/0/4  
as a string:  
- `"po 1"` for port-channel 1  
- `"whatever"` for whatever  

You may enable output of interaction between the PC and a commutator to the console:  
`Commutator.console_print = True`

### Examples

To see the SW version, execute a command and then a script:  
```
from ex_wrapper import Commutator

c = Commutator('192.168.1.1', 'admin', 'password')
print(c.version())
print(c.execute('show mac address-table int gi0/1'))
c.execute_file('script.txt')
```

To see ports with poe devices consuming power and the amount of it:   
```
from ex_wrapper import Commutator

c = Commutator('192.168.1.1', 'admin', 'password')
for i in range(1, 25): # Checking GigabitEthernet ports from 1 to 24
	ans = c.get_poe(i, params=True):
	if ans['status']:
	print(ans['power'])
```

To see vlan setup on ports with active links:  
```
from ex_wrapper import Commutator

c = Commutator('192.168.1.1', 'admin', 'password')
for i in range(1, 25): # Checking GigabitEthernet ports from 1 to 24
	if c.link_state(i):
		print(i, c.get_vlan(i))

```

To set vlan configuration on ports with "Wi-Fi" in description:  
```
from ex_wrapper import Commutator

Commutator.console_print = True
c = Commutator('192.168.1.1', 'admin', 'password')
for i in range(1, 25): # Checking GigabitEthernet ports from 1 to 24
	if "Wi-fi' in c.description(i):
		c.set_vlan(i, {'mode': 'trunk', 'allowed': '102,104,111-112', 'native': 110})
```
