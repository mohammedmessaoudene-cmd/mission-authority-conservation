"""Software-only research reference: consumable mission authority.

NOT a production security boundary, MCP/A2A implementation, TEE attestation,
legal identity service, or payment rail. All effects are toy SQLite rows.
Protocol strings are ASCII, integers are bounded, floats are forbidden.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

MAXINT = 2**53 - 1
MAX_WIRE = 65536


class Denied(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def require(ok: bool, code: str) -> None:
    if not ok:
        raise Denied(code)


def validate_tree(x: Any, depth: int = 0) -> None:
    require(depth <= 16, "DEPTH")
    if x is None or type(x) is bool:
        return
    if type(x) is int:
        require(abs(x) <= MAXINT, "INTEGER_RANGE")
    elif type(x) is str:
        require(x.isascii() and len(x) <= 16384, "ASCII_OR_LENGTH")
    elif type(x) is list:
        require(len(x) <= 1024, "LIST_LENGTH")
        for v in x:
            validate_tree(v, depth + 1)
    elif type(x) is dict:
        require(len(x) <= 64 and all(type(k) is str for k in x), "OBJECT")
        for k, v in x.items():
            validate_tree(k, depth + 1)
            validate_tree(v, depth + 1)
    else:
        raise Denied("UNSUPPORTED_TYPE")


def canon(x: Any) -> bytes:
    """A deliberately restricted ASCII JSON profile, NOT general RFC 8785."""
    validate_tree(x)
    b = json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                   allow_nan=False).encode("ascii")
    require(len(b) <= MAX_WIRE, "WIRE_SIZE")
    return b


def decode(b: bytes) -> Any:
    require(type(b) is bytes and len(b) <= MAX_WIRE, "WIRE_SIZE")
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for k, v in items:
            require(k not in d, "DUPLICATE_KEY")
            d[k] = v
        return d
    def bad_number(_: str) -> None:
        raise Denied("NONINTEGER_NUMBER")
    try:
        x = json.loads(b, object_pairs_hook=pairs, parse_float=bad_number,
                       parse_constant=bad_number)
        canon(x)
        return x
    except Denied:
        raise
    except (ValueError, UnicodeError, RecursionError) as e:
        raise Denied("MALFORMED_JSON") from e


def digest(x: Any) -> str:
    return hashlib.sha256(canon(x)).hexdigest()


def exact(x: Any, names: str) -> None:
    require(type(x) is dict and set(x) == set(names.split()), "SCHEMA")


def natural(x: Any, positive: bool = False) -> None:
    require(type(x) is int and (0 < x if positive else 0 <= x) and x <= MAXINT,
            "NATURAL_NUMBER")


def vector(x: Any) -> list[int]:
    require(type(x) is list and len(x) == 3, "VECTOR")
    for v in x:
        natural(v)
    return x


@dataclass
class Key:
    private: Ed25519PrivateKey

    @classmethod
    def generate(cls) -> "Key":
        return cls(Ed25519PrivateKey.generate())

    @property
    def public(self) -> bytes:
        return self.private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    @property
    def kid(self) -> str:
        return hashlib.sha256(self.public).hexdigest()

    def sign(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        # Freeze a copy so later in-memory caller mutations invalidate the signature.
        p = decode(canon(payload))
        b = b"ATLAB/0.1\x00" + kind.encode("ascii") + b"\x00" + canon({"kid": self.kid, "payload": p})
        return {"kind": kind, "kid": self.kid, "payload": p,
                "signature": self.private.sign(b).hex()}


def verify_public(obj: Any, kind: str, public: bytes) -> dict[str, Any]:
    """Verify with ONLY a pinned raw 32-byte public key; no secret is required."""
    require(type(public) is bytes and len(public) == 32, "PUBLIC_KEY")
    kid = hashlib.sha256(public).hexdigest()
    exact(obj, "kind kid payload signature")
    require(obj["kind"] == kind and obj["kid"] == kid, "SIGNER_OR_DOMAIN")
    require(type(obj["signature"]) is str and len(obj["signature"]) == 128,
            "SIGNATURE_ENCODING")
    require(type(obj["payload"]) is dict, "SCHEMA")
    try:
        sig = bytes.fromhex(obj["signature"])
        require(len(sig) == 64 and sig.hex() == obj["signature"], "SIGNATURE_ENCODING")
        data = b"ATLAB/0.1\x00" + kind.encode("ascii") + b"\x00" + canon({"kid": kid, "payload": obj["payload"]})
        Ed25519PublicKey.from_public_bytes(public).verify(sig, data)
    except (ValueError, InvalidSignature) as e:
        raise Denied("BAD_SIGNATURE") from e
    return decode(canon(obj["payload"]))


def verify(obj: Any, kind: str, key: Key) -> dict[str, Any]:
    # Test-fixture convenience wrapper; verification never uses the private bytes.
    return verify_public(obj, kind, key.public)


@dataclass
class Clock:
    # Trusted clock injected by the laboratory, never a field supplied by the agent.
    value: int = 1000
    def now(self) -> int:
        return self.value


class Database:
    def __init__(self, path: str | Path, clock: Clock):
        self.path, self.clock = str(path), clock
        c = sqlite3.connect(self.path)
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY,v INTEGER)")
        c.execute("INSERT OR IGNORE INTO meta VALUES ('clock',0)")
        c.commit()
        c.close()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        c = sqlite3.connect(self.path, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA synchronous=FULL")
        try:
            c.execute("BEGIN IMMEDIATE")
            n = self.clock.now()
            require(type(n) is int, "CLOCK")
            last = c.execute("SELECT v FROM meta WHERE k='clock'").fetchone()[0]
            require(n >= last, "CLOCK_ROLLBACK")
            c.execute("UPDATE meta SET v=? WHERE k='clock'", (n,))
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()


def invocation(iid: str, actor: Key, cap: str = "root", mission: str = "root",
               op: str = "pay", target: str = "vendor-a", amount: int = 10,
               deadline: int = 1100, policy: str = "policy-v1", aud: str = "tool-demo",
               params: dict[str, Any] | None = None) -> dict[str, Any]:
    if params is None:
        params = {"amount_minor": amount} if op == "pay" else (
            {"dataset": "dataset-a"} if op == "export" else {"message": "hello"})
    return {"iid": iid, "mission": mission, "cap": cap, "actor": actor.kid,
            "aud": aud, "op": op, "target": target, "params": params,
            "deadline": deadline, "policy": policy}


def validate_invocation(p: dict[str, Any]) -> None:
    exact(p, "iid mission cap actor aud op target params deadline policy")
    canon(p)
    for k in ("iid", "mission", "cap", "actor", "aud", "op", "target", "policy"):
        require(type(p[k]) is str and 0 < len(p[k]) <= 128, "IDENTIFIER")
    natural(p["deadline"], True)
    require(type(p["params"]) is dict, "SCHEMA")


class ToyResource(Database):
    """An honest resource with durable idempotence and transactional TOY effects.

    The resource, not the LLM, computes the effect vector. This is not an SMTP,
    bank, filesystem, or physical-actuator atomicity implementation.
    """
    DATASETS = {"dataset-a": b"a" * 80, "dataset-b": b"b" * 240}

    def __init__(self, path: str | Path, clock: Clock, key: Key, gate_key: Key,
                 audience: str = "tool-demo", version: str = "resource-v1"):
        super().__init__(path, clock)
        self.key, self.gate_key = key, gate_key
        self.audience, self.version = audience, version
        with self.tx() as c:
            c.execute("CREATE TABLE IF NOT EXISTS results (iid TEXT PRIMARY KEY, hash TEXT, receipt TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS effects (iid TEXT PRIMARY KEY,c0 INTEGER,c1 INTEGER,c2 INTEGER)")

    def estimate(self, p: dict[str, Any]) -> list[int]:
        validate_invocation(p)
        require(p["aud"] == self.audience, "AUDIENCE")
        if p["op"] == "pay":
            exact(p["params"], "amount_minor")
            natural(p["params"]["amount_minor"], True)
            return [p["params"]["amount_minor"], 0, 1]
        if p["op"] == "export":
            exact(p["params"], "dataset")
            require(type(p["params"]["dataset"]) is str and p["params"]["dataset"] in self.DATASETS,
                    "DATASET")
            return [0, len(self.DATASETS[p["params"]["dataset"]]), 1]
        if p["op"] == "send":
            exact(p["params"], "message")
            require(type(p["params"]["message"]) is str, "MESSAGE")
            return [0, len(p["params"]["message"].encode("ascii")), 1]
        raise Denied("OPERATION")

    def prepare(self, p: dict[str, Any]) -> dict[str, Any]:
        costs = self.estimate(p)
        require(self.clock.now() < p["deadline"], "EXPIRED")
        return self.key.sign("PREPARED", {"action_hash": digest(p), "cost": costs,
            "resource_version": self.version, "expires": p["deadline"], "aud": self.audience})

    def apply(self, p: dict[str, Any], prepared: dict[str, Any], permit: dict[str, Any]) -> dict[str, Any]:
        pr = verify(prepared, "PREPARED", self.key)
        t = verify(permit, "DISPATCH", self.gate_key)
        exact(t, "iid action_hash preview_hash cost aud cap epoch expires resource_version")
        require(t["iid"] == p["iid"] and t["action_hash"] == digest(p), "ACTION_BINDING")
        require(t["preview_hash"] == digest(pr) and pr["action_hash"] == digest(p), "PREVIEW_BINDING")
        require(t["aud"] == self.audience and t["cap"] == p["cap"], "AUDIENCE")
        require(t["cost"] == pr["cost"], "COST_BINDING")
        with self.tx() as c:
            row = c.execute("SELECT hash,receipt FROM results WHERE iid=?", (p["iid"],)).fetchone()
            if row:
                require(row["hash"] == digest(p), "IDEMPOTENCY_CONFLICT")
                return json.loads(row["receipt"])
            # Precondition rejection is DURABLY recorded. A later replay cannot
            # turn NOT_APPLIED into APPLIED after a version/clock change.
            ok = (self.clock.now() < t["expires"] and self.clock.now() < pr["expires"]
                  and pr["resource_version"] == self.version
                  and t["resource_version"] == self.version
                  and self.estimate(p) == pr["cost"])
            result = "APPLIED" if ok else "NOT_APPLIED"
            rec = self.key.sign("RECEIPT", {"iid": p["iid"], "action_hash": digest(p),
                "preview_hash": digest(pr), "cost": pr["cost"], "result": result,
                "epoch": t["epoch"], "aud": self.audience})
            c.execute("INSERT INTO results VALUES(?,?,?)", (p["iid"], digest(p), json.dumps(rec)))
            if ok:
                c.execute("INSERT INTO effects VALUES(?,?,?,?)", (p["iid"], *pr["cost"]))
            return rec

    def receipt(self, iid: str) -> dict[str, Any] | None:
        with self.tx() as c:
            r = c.execute("SELECT receipt FROM results WHERE iid=?", (iid,)).fetchone()
            return json.loads(r[0]) if r else None

    def totals(self) -> list[int]:
        with self.tx() as c:
            return list(c.execute("SELECT COALESCE(SUM(c0),0),COALESCE(SUM(c1),0),COALESCE(SUM(c2),0) FROM effects").fetchone())


class Gate(Database):
    """Single-authority serialization domain, with durable reservations.

    Keys are software objects. The laboratory pins roles directly; no PKI,
    DID method, HSM, WebAuthn ceremony, RATS quote or vendor claim is simulated
    as if it were real hardware evidence.
    """
    def __init__(self, path: str | Path, clock: Clock, key: Key, principal: Key,
                 human: Key, resource_key: Key, actors: dict[str, Key],
                 policy: str = "policy-v1", resource_version: str = "resource-v1"):
        super().__init__(path, clock)
        self.key, self.principal, self.human, self.resource_key = key, principal, human, resource_key
        self.actors, self.policy, self.resource_version = actors, policy, resource_version
        with self.tx() as c:
            c.execute("INSERT OR IGNORE INTO meta VALUES ('epoch',1)")
            c.execute("""CREATE TABLE IF NOT EXISTS caps (
                id TEXT PRIMARY KEY,parent TEXT,subject TEXT,aud TEXT,ops TEXT,dest TEXT,
                expires INTEGER,revoked INTEGER,b0 INTEGER,b1 INTEGER,b2 INTEGER,
                f0 INTEGER,f1 INTEGER,f2 INTEGER,c0 INTEGER,c1 INTEGER,c2 INTEGER)""")
            c.execute("""CREATE TABLE IF NOT EXISTS actions (
                iid TEXT PRIMARY KEY, hash TEXT, cap TEXT, preview_hash TEXT,
                c0 INTEGER,c1 INTEGER,c2 INTEGER, epoch INTEGER,expires INTEGER,
                aud TEXT,version TEXT,state TEXT, receipt TEXT,policy TEXT)""")
            c.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY,prev TEXT,body TEXT,hash TEXT)")

    def _event(self, c: sqlite3.Connection, body: dict[str, Any]) -> None:
        row = c.execute("SELECT seq,hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        seq, prev = (row[0] + 1, row[1]) if row else (1, "0" * 64)
        encoded = canon(body).decode()
        h = digest({"seq": seq, "prev": prev, "body": body})
        c.execute("INSERT INTO events VALUES(?,?,?,?)", (seq, prev, encoded, h))

    def epoch(self) -> int:
        with self.tx() as c:
            return c.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0]

    def _chain(self, c: sqlite3.Connection, cap: str) -> tuple[sqlite3.Row, str]:
        first = None
        seen: set[str] = set()
        while True:
            require(cap not in seen and len(seen) <= 16, "CAP_CHAIN")
            seen.add(cap)
            row = c.execute("SELECT * FROM caps WHERE id=?", (cap,)).fetchone()
            require(row is not None, "UNKNOWN_CAP")
            require(not row["revoked"], "REVOKED")
            require(self.clock.now() < row["expires"], "CAP_EXPIRED")
            if first is None:
                first = row
            if row["parent"] is None:
                return first, row["id"]
            cap = row["parent"]

    def issue(self, signed: dict[str, Any]) -> None:
        p = verify(signed, "MISSION", self.principal)
        exact(p, "id subject aud ops dest expires budget")
        vector(p["budget"])
        require(p["subject"] in self.actors, "ACTOR")
        self._scope(p)
        with self.tx() as c:
            require(c.execute("SELECT 1 FROM caps WHERE id=?", (p["id"],)).fetchone() is None, "CAP_EXISTS")
            c.execute("INSERT INTO caps VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (p["id"], None, p["subject"], p["aud"], json.dumps(p["ops"]),json.dumps(p["dest"]),
                 p["expires"], 0, *p["budget"], *p["budget"], 0, 0, 0))
            self._event(c, {"type": "ISSUE", "cap": p["id"], "budget": p["budget"]})

    def _scope(self, p: dict[str, Any]) -> None:
        require(type(p["id"]) is str and 0 < len(p["id"]) <= 128, "IDENTIFIER")
        natural(p["expires"], True)
        require(p["expires"] > self.clock.now(), "EXPIRED")
        for field in ("ops", "dest"):
            require(type(p[field]) is list and p[field] and
                all(type(s) is str and 0 < len(s) <= 128 for s in p[field]) and
                len(set(p[field])) == len(p[field]), "SCOPE")
        require(set(p["ops"]) <= {"pay", "send", "export"}, "OPERATION")
        require(type(p["aud"]) is str and p["aud"] == "tool-demo", "AUDIENCE")

    def delegate(self, signed: dict[str, Any]) -> None:
        # Load only a candidate issuer from signed payload, then verify it
        # against the trusted parent subject before using requested rights.
        exact(signed, "kind kid payload signature")
        candidate = signed["payload"]
        exact(candidate, "parent id subject aud ops dest expires budget")
        with self.tx() as c:
            parent, _ = self._chain(c, candidate["parent"])
            p = verify(signed, "DELEGATE", self.actors[parent["subject"]])
            self._scope(p)
            vector(p["budget"])
            require(p["subject"] in self.actors, "ACTOR")
            require(p["aud"] == parent["aud"] and set(p["ops"]) <= set(json.loads(parent["ops"]))
                    and set(p["dest"]) <= set(json.loads(parent["dest"]))
                    and p["expires"] <= parent["expires"], "DELEGATION_WIDENING")
            require(c.execute("SELECT 1 FROM caps WHERE id=?", (p["id"],)).fetchone() is None, "CAP_EXISTS")
            require(all(p["budget"][i] <= parent[f"f{i}"] for i in range(3)), "BUDGET")
            c.execute("UPDATE caps SET f0=f0-?,f1=f1-?,f2=f2-? WHERE id=?", (*p["budget"], parent["id"]))
            c.execute("INSERT INTO caps VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (p["id"],parent["id"],p["subject"],p["aud"],json.dumps(p["ops"]),json.dumps(p["dest"]),
                 p["expires"],0,*p["budget"],*p["budget"],0,0,0))
            self._event(c, {"type": "DELEGATE", "parent": parent["id"], "cap": p["id"], "budget": p["budget"]})

    def _authenticate(self, signed: dict[str, Any], preview: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        exact(signed, "kind kid payload signature")
        require(type(signed["kid"]) is str and signed["kid"] in self.actors, "ACTOR")
        p = verify(signed, "INVOKE", self.actors[signed["kid"]])
        validate_invocation(p)
        require(p["actor"] == signed["kid"], "ACTOR_BINDING")
        pr = verify(preview, "PREPARED", self.resource_key)
        exact(pr, "action_hash cost resource_version expires aud")
        vector(pr["cost"])
        require(pr["action_hash"] == digest(p), "ACTION_BINDING")
        require(pr["expires"] == p["deadline"] and pr["aud"] == p["aud"], "PREVIEW_BINDING")
        require(pr["resource_version"] == self.resource_version, "RESOURCE_VERSION")
        require(p["policy"] == self.policy, "POLICY_VERSION")
        require(self.clock.now() < p["deadline"], "EXPIRED")
        return p, pr

    def reserve(self, signed: dict[str, Any], preview: dict[str, Any],
                approval: dict[str, Any] | None = None) -> str:
        p, pr = self._authenticate(signed, preview)
        with self.tx() as c:
            cap, root = self._chain(c, p["cap"])
            require(p["mission"] == root, "MISSION_BINDING")
            require(p["actor"] == cap["subject"], "SUBJECT")
            require(p["aud"] == cap["aud"], "AUDIENCE")
            require(p["op"] in json.loads(cap["ops"]) and p["target"] in json.loads(cap["dest"]), "SCOPE")
            epoch = c.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0]
            effective_expiry = min(p["deadline"], cap["expires"])
            high = p["op"] == "export" or pr["cost"][0] >= 50
            if high:
                require(approval is not None, "HUMAN_REQUIRED")
                ap = verify(approval, "APPROVE", self.human)
                exact(ap, "action_hash preview_hash cap epoch expires decision")
                require(ap["action_hash"] == digest(p) and ap["preview_hash"] == digest(pr)
                        and ap["cap"] == p["cap"] and ap["epoch"] == epoch
                        and ap["decision"] == "approve", "APPROVAL_BINDING")
                natural(ap["expires"], True)
                require(self.clock.now() < ap["expires"] <= p["deadline"], "APPROVAL_EXPIRED")
                effective_expiry = min(effective_expiry, ap["expires"])
            old = c.execute("SELECT hash,state FROM actions WHERE iid=?", (p["iid"],)).fetchone()
            if old:
                require(old["hash"] == digest(p), "IDEMPOTENCY_CONFLICT")
                return old["state"]
            cost = pr["cost"]
            require(all(cost[i] <= cap[f"f{i}"] for i in range(3)), "BUDGET")
            c.execute("UPDATE caps SET f0=f0-?,f1=f1-?,f2=f2-? WHERE id=?", (*cost, cap["id"]))
            c.execute("INSERT INTO actions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (p["iid"],digest(p),p["cap"],digest(pr),*cost,epoch,effective_expiry,p["aud"],
                 pr["resource_version"],"RESERVED",None,p["policy"]))
            self._event(c, {"type": "RESERVE", "iid": p["iid"], "cost": cost})
            return "RESERVED"

    def begin(self, iid: str) -> dict[str, Any]:
        with self.tx() as c:
            r = c.execute("SELECT * FROM actions WHERE iid=?", (iid,)).fetchone()
            require(r is not None, "UNKNOWN_ACTION")
            require(r["state"] == "RESERVED", "NO_REDISPATCH")
            self._chain(c, r["cap"])
            epoch = c.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0]
            require(r["epoch"] == epoch, "STALE_EPOCH")
            require(self.clock.now() < r["expires"], "EXPIRED")
            require(r["version"] == self.resource_version, "RESOURCE_VERSION")
            require(r["policy"] == self.policy, "POLICY_VERSION")
            # State is durable before the permit leaves this method.
            c.execute("UPDATE actions SET state='DISPATCHED' WHERE iid=?", (iid,))
            self._event(c, {"type": "DISPATCH", "iid": iid})
            return self.key.sign("DISPATCH", {"iid": iid,"action_hash":r["hash"],
                "preview_hash":r["preview_hash"],"cost":[r[f"c{i}"] for i in range(3)],
                "aud":r["aud"],"cap":r["cap"],"epoch":epoch,"expires":r["expires"],
                "resource_version":r["version"]})

    def mark_unknown(self, iid: str) -> None:
        with self.tx() as c:
            r = c.execute("SELECT state FROM actions WHERE iid=?", (iid,)).fetchone()
            require(r is not None and r["state"] in ("DISPATCHED", "UNKNOWN"), "STATE")
            c.execute("UPDATE actions SET state='UNKNOWN' WHERE iid=?", (iid,))
            self._event(c, {"type":"UNKNOWN", "iid":iid})

    def cancel(self, iid: str) -> None:
        with self.tx() as c:
            r = c.execute("SELECT * FROM actions WHERE iid=?", (iid,)).fetchone()
            require(r is not None and r["state"] == "RESERVED", "UNSAFE_REFUND")
            c.execute("UPDATE caps SET f0=f0+?,f1=f1+?,f2=f2+? WHERE id=?",
                      (*(r[f"c{i}"] for i in range(3)),r["cap"]))
            c.execute("UPDATE actions SET state='ABORTED' WHERE iid=?", (iid,))
            self._event(c,{"type":"CANCEL", "iid":iid})

    def settle(self, signed: dict[str, Any]) -> str:
        p = verify(signed,"RECEIPT",self.resource_key)
        exact(p,"iid action_hash preview_hash cost result epoch aud")
        vector(p["cost"])
        require(p["result"] in ("APPLIED","NOT_APPLIED"),"RESULT")
        with self.tx() as c:
            r = c.execute("SELECT * FROM actions WHERE iid=?",(p["iid"],)).fetchone()
            require(r is not None,"UNKNOWN_ACTION")
            require(p["action_hash"] == r["hash"] and p["preview_hash"] == r["preview_hash"]
                    and p["cost"] == [r[f"c{i}"] for i in range(3)]
                    and p["epoch"] == r["epoch"] and p["aud"] == r["aud"],"RECEIPT_BINDING")
            state = "COMMITTED" if p["result"] == "APPLIED" else "ABORTED"
            if r["state"] in ("COMMITTED","ABORTED"):
                require(r["state"] == state and r["receipt"] == json.dumps(signed,sort_keys=True),"RECEIPT_CONFLICT")
                return state
            require(r["state"] in ("DISPATCHED","UNKNOWN"),"STATE")
            fields = "c" if state == "COMMITTED" else "f"
            c.execute(f"UPDATE caps SET {fields}0={fields}0+?,{fields}1={fields}1+?,{fields}2={fields}2+? WHERE id=?",
                      (*p["cost"],r["cap"]))
            c.execute("UPDATE actions SET state=?,receipt=? WHERE iid=?",
                      (state,json.dumps(signed,sort_keys=True),p["iid"]))
            self._event(c,{"type":state,"iid":p["iid"]})
            return state

    def revoke(self, signed: dict[str, Any]) -> None:
        p = verify(signed,"REVOKE",self.principal)
        exact(p,"cap epoch")
        natural(p["epoch"],True)
        with self.tx() as c:
            epoch = c.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0]
            require(p["epoch"] == epoch + 1,"REVOCATION_EPOCH")
            require(c.execute("SELECT 1 FROM caps WHERE id=?",(p["cap"],)).fetchone() is not None,"UNKNOWN_CAP")
            c.execute("UPDATE caps SET revoked=1 WHERE id=?",(p["cap"],))
            # A deliberately conservative global generation fence. It also
            # invalidates reservations in unrelated missions (availability cost).
            c.execute("UPDATE meta SET v=? WHERE k='epoch'",(p["epoch"],))
            self._event(c,{"type":"REVOKE",**p})

    def state(self, iid: str) -> str | None:
        with self.tx() as c:
            r=c.execute("SELECT state FROM actions WHERE iid=?",(iid,)).fetchone()
            return r[0] if r else None

    def balance(self, cap: str = "root") -> dict[str,list[int]]:
        with self.tx() as c:
            r=c.execute("SELECT * FROM caps WHERE id=?",(cap,)).fetchone()
            require(r is not None,"UNKNOWN_CAP")
            return {name:[r[f"{prefix}{i}"] for i in range(3)]
                    for name,prefix in (("budget","b"),("free","f"),("committed","c"))}

    def audit(self) -> dict[str,int]:
        """Independent accounting identity, checked on persisted rows.

        This verifies internal consistency, NOT the truth of a malicious
        resource, rollback-proof storage, or externally witnessed log coverage.
        """
        with self.tx() as c:
            caps=c.execute("SELECT * FROM caps").fetchall()
            for r in caps:
                children=c.execute("SELECT COALESCE(SUM(b0),0),COALESCE(SUM(b1),0),COALESCE(SUM(b2),0) FROM caps WHERE parent=?",(r["id"],)).fetchone()
                pending=c.execute("SELECT COALESCE(SUM(c0),0),COALESCE(SUM(c1),0),COALESCE(SUM(c2),0) FROM actions WHERE cap=? AND state IN ('RESERVED','DISPATCHED','UNKNOWN')",(r["id"],)).fetchone()
                for i in range(3):
                    require(r[f"f{i}"] >= 0 and r[f"c{i}"] >= 0,"NEGATIVE_BALANCE")
                    require(r[f"b{i}"] == r[f"f{i}"] + r[f"c{i}"] + children[i] + pending[i],"CONSERVATION")
            prev="0"*64
            rows=c.execute("SELECT * FROM events ORDER BY seq").fetchall()
            for seq,r in enumerate(rows,1):
                require(r["seq"] == seq and r["prev"] == prev,"EVENT_CHAIN")
                require(r["hash"] == digest({"seq":seq,"prev":prev,"body":json.loads(r["body"])}),"EVENT_CHAIN")
                prev=r["hash"]
            return {"caps":len(caps),"actions":c.execute("SELECT count(*) FROM actions").fetchone()[0],"events":len(rows)}
