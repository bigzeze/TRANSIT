orgspeed = 13.89
s0 = 7.5
beta = 0.1
tr = 1
newspeed = (orgspeed*s0*beta/(s0+tr*orgspeed))/(1-orgspeed*tr*beta/(s0+tr*orgspeed))
print(newspeed)