from ex_wrapper import Commutator

c = Commutator('192.168.20.61', 'admin', '306am6ya')
#c = Commutator('192.168.111.57', 'karlov', 'karlov')
print(c.version())

Commutator.console_print = True
for i in range(9, 10):
		print(i, c.get_poe(i, mode='verbose'))
