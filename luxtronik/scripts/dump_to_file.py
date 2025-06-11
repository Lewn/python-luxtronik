# -*- coding: utf-8 -*-
"""
@author: lloopik
"""

from luxtronik import Luxtronik
from luxtronik.constants import LUXTRONIK_DEFAULT_PORT
from contextlib import redirect_stdout
from heatpump import dump_websocket
from datetime import datetime

def dump_luxtronik(ip, port=LUXTRONIK_DEFAULT_PORT):
    client = Luxtronik(ip, port)
    calculations, parameters, visibilities = client.read()

    print("=" * 80)
    print(f"{' Parameter ': ^80}")
    print("=" * 80)

    for number, param in parameters:
        print(
            f"Number: {number:<5} Name: {param.name:<60} "
            + f"Type: {param.__class__.__name__:<20} Value: {param.raw}"
        )

    print("=" * 80)
    print(f"{' Calculations ': ^80}")
    print("=" * 80)

    for number, calc in calculations:
        print(
            f"Number: {number:<5} Name: {calc.name:<60} "
            + f"Type: {calc.__class__.__name__:<20} Value: {calc.raw}"
        )

    print("=" * 80)
    print(f"{' Visibilities ': ^80}")
    print("=" * 80)

    for number, visi in visibilities:
        print(
            f"Number: {number:<5} Name: {visi.name:<60} "
            + f"Type: {visi.__class__.__name__:<20} Value: {visi.raw}"
        )


datetime.now()
fname = datetime.now().strftime('dumps/dump_%Y%m%d_%H%M%S.log')
with open(fname, 'w') as f, redirect_stdout(f):
    dump_websocket("192.168.6.157")
    dump_luxtronik("192.168.6.157")
