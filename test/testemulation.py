import unittest
import os
import subprocess
import socket
import time
import shutil

from testzcc import ZccBaseTestCase

# Store testdir for safe switch back to directory:
testdir = os.path.dirname(os.path.abspath(__file__))

def tryrm(fn):
    try:
        os.remove(fn)
    except OSError:
        pass

qemu_app = 'qemu-system-arm'

def has_qemu():
    """ Determines if qemu is possible """
    if not hasattr(shutil, 'which'):
        return False
    return bool(shutil.which(qemu_app))


def runQemu(kernel, machine='lm3s811evb'):
    """ Runs qemu on a given kernel file """

    if not has_qemu():
        return ''
    tryrm('qemucontrol.sock')
    tryrm('qemuserial.sock')

    # Listen to the control socket:
    qemu_control_serve = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    qemu_control_serve.bind('qemucontrol.sock')
    qemu_control_serve.listen(0)

    # Listen to the serial output:
    qemu_serial_serve = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    qemu_serial_serve.bind('qemuserial.sock')
    qemu_serial_serve.listen(0)

    args = [qemu_app, '-M', machine, '-m', '16M',
        '-nographic',
        '-kernel', kernel,
        '-monitor', 'unix:qemucontrol.sock',
        '-serial', 'unix:qemuserial.sock',
        '-S']
    p = subprocess.Popen(args)

    #qemu_serial Give process some time to boot:
    qemu_serial_serve.settimeout(3)
    qemu_control_serve.settimeout(3)
    qemu_serial, address_peer = qemu_serial_serve.accept()
    qemu_control, address_peer = qemu_control_serve.accept()

    # Give the go command:
    qemu_control.send('cont\n'.encode('ascii'))

    qemu_serial.settimeout(0.2)

    # Receive all data:
    data = bytearray()
    for i in range(400):
        try:
            data += qemu_serial.recv(1)
        except socket.timeout as e:
            break
    data = data.decode('ascii', errors='ignore')
    # print(data)

    # Send quit command:
    qemu_control.send("quit\n".encode('ascii'))
    if hasattr(subprocess, 'TimeoutExpired'):
        try:
            p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            p.kill()
    else:
        time.sleep(2)
        p.kill()
    qemu_control.close()
    qemu_serial.close()
    qemu_control_serve.close()
    qemu_serial_serve.close()

    tryrm('qemucontrol.sock')
    tryrm('qemuserial.sock')

    # Check that output was correct:
    return data


class EmulationTestCase(ZccBaseTestCase):
    """ Tests the compiler driver """
    def setUp(self):
        if not has_qemu():
            self.skipTest('Not running Qemu test')

    def testM3Bare(self):
        self.skipTest('TODO')
        """ Build bare m3 binary and emulate it """
        recipe = os.path.join(testdir, 'm3_bare', 'build.xml')
        self.buildRecipe(recipe)
        data = runQemu('m3_bare/bare.bin')
        self.assertEqual('Hello worle', data)

    def testA9Bare(self):
        self.skipTest('TODO')
        """ Build vexpress cortex-A9 binary and emulate it """
        recipe = os.path.join(testdir, '..', 'examples', 'qemu_a9_hello',
            'build.xml')
        self.buildRecipe(recipe)
        data = runQemu('../examples/qemu_a9_hello/hello.bin',
            machine='vexpress-a9')
        self.assertEqual('Hello worle', data)


if __name__ == '__main__':
    unittest.main()