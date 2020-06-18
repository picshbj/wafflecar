f = open('network', 'r')
o = open('network2', 'w')

for line in f:    
    o.write(line)

    if 'bridge' in line:
        o.write("        option ifname 'eth0'\n")

f.close()
o.close()
