"""Spawned local resource fixture. Not a sandbox, transport protocol, or remote API.

The test supplies an ephemeral resource key and only the gate public key to the
child. No private key is written to disk. Pipe messages are trusted test commands;
this interface MUST NOT be exposed to untrusted clients.
"""
from __future__ import annotations
import hashlib, multiprocessing, os
from pathlib import Path
from types import SimpleNamespace
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from .core import Clock, Key, ToyResource

def _worker(pipe, db: str, resource_secret: bytes, gate_public: bytes, initial_now: int):
    clock=Clock(initial_now)
    key=Key(Ed25519PrivateKey.from_private_bytes(resource_secret))
    public=SimpleNamespace(public=gate_public,kid=hashlib.sha256(gate_public).hexdigest())
    resource=ToyResource(Path(db),clock,key,public)
    try:
        while True:
            command=pipe.recv()
            clock.value=command.get('now',clock.value)
            op=command['op']
            if op=='stop': return
            if op=='apply':
                receipt=resource.apply(command['action'],command['prepared'],command['permit'])
                if command.get('exit_after_commit',False):
                    os._exit(73)  # transaction returned before controlled lost reply
                pipe.send(receipt)
            elif op=='receipt': pipe.send(resource.receipt(command['iid']))
            elif op=='totals': pipe.send(resource.totals())
            else: raise ValueError('Unknown fixture operation')
    finally: pipe.close()

class ResourceProcess:
    def __init__(self, db: Path, resource_key: Key, gate_public: bytes, initial_now: int=1000):
        context=multiprocessing.get_context('spawn')
        parent,child=context.Pipe()
        secret=resource_key.private.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())
        self.pipe=parent
        self.process=context.Process(target=_worker,args=(child,str(db),secret,gate_public,initial_now),daemon=True)
        self.process.start();child.close()
    def send(self, **command): self.pipe.send(command)
    def receive(self, timeout: float=15):
        if not self.pipe.poll(timeout): raise TimeoutError('Local test worker did not reply')
        return self.pipe.recv()
    def call(self, **command):
        self.send(**command)
        return self.receive()
    def close(self):
        if self.process.is_alive():
            try: self.pipe.send({'op':'stop'})
            except (BrokenPipeError,EOFError,OSError): pass
        self.process.join(5)
        if self.process.is_alive(): self.process.terminate();self.process.join(5)
        self.pipe.close()
    def __enter__(self): return self
    def __exit__(self, *args): self.close()
