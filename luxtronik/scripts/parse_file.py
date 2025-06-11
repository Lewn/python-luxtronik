# -*- coding: utf-8 -*-
"""
@author: lloopik
"""

import numpy as np
from xml.dom.minidom import parseString
import re
import glob
from scipy.stats import linregress
import matplotlib.pyplot as plt
import plthelper
import operator

plthelper.init()

units = ['°C',
         ' K',
         ' V',
         ' h',
         ' min',
         ' Hz',
         ' l/h',
         ' bar',
         ' %',
         ' kW',
         ' kWh']

binary = [('Aan', 'Uit'),
          ('Ja', 'Nee')]

time = re.compile(r"^([0-9]+):([0-9][0-9])(:[0-9][0-9])?$")

numval = re.compile(r"^Number: ([0-9]+) .*?Value: (-?[0-9]+)$")

def parseValue(value):
    for unit in units:
        if value.endswith(unit):
            return float(value[:-len(unit)])
    for y, n in binary:
        if value == y:
            return 1
        if value == n:
            return 0

    if m := time.match(value):
        m = m.groups()
        secs = int(m[0])*3600 + int(m[1])*60
        if m[2] is not None:
            secs += int(m[2][1:])
        return secs

    if value.endswith('h'):
        try:
            return int(value[:-1])
        except ValueError:
            pass

    try:
        return float(value)
    except ValueError:
        pass
    return None


def readlog(fname):
    with open(fname) as f:
        web = {}
        f = iter(f)
        for line in f:
            if line.startswith('<Content>'):
                tree = parseString(line)

                for elem in tree.getElementsByTagName('value'):
                    if elem.firstChild is None or elem.firstChild.nodeValue is None:
                        continue
                    value = elem.firstChild.nodeValue
                    name = []
                    while (elem := elem.parentNode).tagName == 'item':
                        for child in elem.childNodes:
                            if child.tagName == 'name':
                                name.append(child.firstChild.nodeValue)
                    name = "_".join(reversed(name))
                    value = parseValue(value)
                    if value is not None:
                        web[name] = value

            elif line.startswith('========'):
                break

        #params
        sock = {}
        assert next(f).strip() == "Parameter"
        next(f)
        for line in f:
            if line.startswith('========'):
                break

            m = numval.match(line)
            num, val = m.groups()
            sock[f'p{num}'] = int(val)

        assert next(f).strip() == "Calculations"
        next(f)
        for line in f:
            if line.startswith('========'):
                break

            m = numval.match(line)
            num, val = m.groups()
            sock[f'c{num}'] = int(val)

        assert next(f).strip() == "Visibilities"
        next(f)
        for line in f:
            if line.startswith('========'):
                break

            m = numval.match(line)
            num, val = m.groups()
            sock[f'v{num}'] = int(val)

    return web, sock


i = 0
web, sock = {}, {}
for i, fname in enumerate(glob.glob('dumps/*.log')):
    iweb, isock = readlog(fname)
    for k in web:
        web[k].append(iweb.pop(k, None))
    for k in sock:
        sock[k].append(isock.pop(k, None))

    for k, v in iweb.items():
        web[k] = [None]*i + [v]

    for k, v in isock.items():
        sock[k] = [None]*i + [v]

delsocks = []
for nsock, vsock in sock.items():
    if None in vsock:
        print(f"{nsock} has None values, skipping!!!")
        delsocks.append(nsock)
        continue

    vsock = np.array(vsock)

    if np.all(vsock == vsock[0]):
        # print(f"{nsock} is constant, skipping!!!")
        delsocks.append(nsock)
        continue

for nsock in delsocks:
    del sock[nsock]

matrix = {}
for nweb, vweb in web.items():
    if None in vweb:
        print(f"{nweb} has None values, skipping!!!")
        continue

    vweb = np.array(vweb)

    if np.all(vweb == vweb[0]):
        # print(f"{nweb} is constant, skipping!!!")
        continue

    candidates = []


    for nsock, vsock in sock.items():
        vsock = np.array(vsock)
        slope, intercept, r, p, se = linregress(vweb, vsock)

        candidates.append((r, nsock, intercept, slope))

        matrix[nweb, nsock] = (vweb, vsock, slope, intercept, r)


        for nsock2, vsock2 in sock.items():
            vsock2 = np.array(vsock2)

            for op in [operator.add, operator.mul, operator.truediv, operator.sub]:

                if operator is not operator.truediv and nsock2 > nsock:
                    continue

                vsock3 = op(vsock, vsock2)
                if np.any(np.isnan(vsock3)):
                    continue

                slope, intercept, r, p, se = linregress(vweb, vsock3)

                if np.isnan(r) or slope < 1e-3:
                    continue

                nsock3 = f"Z_{nsock}_{nsock2}_{op.__name__}"

                candidates.append((r, nsock3, intercept, slope))

                matrix[nweb, nsock3] = (vweb, vsock3, slope, intercept, r)

    candidates.sort(reverse=True)
    print(nweb)
    for i, candidate in enumerate(candidates):
        if candidate[0] < 0.999 or i > 5:
            break
        print("    ", candidate)


def plot(nweb, nsock):
    vweb, vsock, slope, intercept, r = matrix[nweb, nsock]

    plt.figure()

    plt.plot(vweb, vsock, '*')
    plt.plot(vweb, vweb*slope+intercept, '.')
    plt.plot((vsock-intercept)/slope, vsock, '.')

    plt.title(f"{nweb} vs {nsock} [R={r}]")

# plot("energiemonitor_energiemonitor_Energie_Energie_Verwarmen", "c151")
# plot("energiemonitor_energiemonitor_Energie_Energie_Warmwater", "c152")

# plot("energiemonitor_energiemonitor_Gebruikte energie_Gebruikte energie_Verwarmen", "c151")
# plot("energiemonitor_energiemonitor_Gebruikte energie_Gebruikte energie_Warmwater", "c152")
