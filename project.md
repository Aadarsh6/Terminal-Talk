# P2P Encrypted Chat — Project Documentation

## Overview

An educational peer-to-peer encrypted messaging system built from low-level Python networking primitives. The goal is to understand and implement the networking stack rather than hiding it behind WebRTC, PeerJS, or a high-level P2P framework.

### Final target

Two real computers should be able to discover each other, establish a direct connection when possible, authenticate cryptographic identities, communicate over an encrypted channel, persist encrypted conversation history locally, and use a relay when direct connectivity is impossible.

**Educational project — not Signal-level security.**

## Architecture

```text
                 ┌──────────────────────┐
                 │  Rendezvous Server   │
                 │ Discovery / Signaling│
                 └──────────┬───────────┘
                            │
                     discovery information
                       ↙          ↘
                  ┌────────┐   ┌────────┐
                  │ Peer A │◄─►│ Peer B │
                  └────────┘   └────────┘
                       actual P2P chat
```

Transport:

```text
Application
 ↓
Peer management
 ↓
Cryptographic identity
 ↓
PyNaCl Box
 ↓
Custom message framing
 ↓
TCP sockets
 ↓
IP networking
 ↓
NAT / firewall / traversal
```

Local storage:

```text
Message → SecretBox → SQLite
```

If direct P2P fails, a relay should forward already-encrypted traffic without needing plaintext or private keys.

# Completed

## TCP fundamentals

Implemented TCP server/client sockets, `bind()`, `listen()`, `accept()`, `connect()`, `sendall()`, `recv()`, blocking sockets, and threaded receive handling.

## TCP message framing

Messages use:

```text
[4-byte length][message bytes]
```

`protocol.py` implements `send_message()` and `recv_message()` using `struct.pack("!I", ...)` and `struct.unpack("!I", ...)`.

TCP is a byte stream, so framing creates application-level message boundaries.

## Threaded communication

The receive loop runs separately from the input/send loop, allowing both peers to send and receive concurrently.

## Encrypted transport

PyNaCl `Box` provides public-key authenticated encryption. Each peer has a private/public key pair; public keys are exchanged and private keys remain local.

## Persistent cryptographic identity

`identity.py` persists each peer's private key. Restarting the application therefore preserves the same cryptographic identity.

## Fingerprint verification

A SHA-256 fingerprint of the peer's public key is displayed for manual verification. This is a TOFU/manual trust model, conceptually similar to SSH host-key verification, not Signal's identity-verification system.

## SQLite history

Conversation history is stored locally in SQLite and associated with the peer's cryptographic fingerprint rather than its IP address.

## Encrypted local history

Messages are encrypted with PyNaCl `SecretBox` before being stored in SQLite. The storage key is separate from the transport identity key.

## Restart persistence

Verified flow:

```text
TCP → framing → encrypted communication
→ persistent identity → fingerprint verification
→ encrypted SQLite history → restart → history loads again
```

# Current code structure

```text
p2p-chat/
├── client.py
├── server.py
├── protocol.py
├── identity.py
├── storage.py
├── rendezvous_server.py
├── rendezvous_test.py
├── crypto_test.py
├── README.md
├── project.md
└── .gitignore
```

Local secrets/databases such as `*.bin` and `*.db` should not be committed.

### Responsibilities

- `protocol.py` — framing.
- `identity.py` — persistent transport identity and storage keys.
- `storage.py` — encrypted SQLite history.
- `client.py` / `server.py` — current chat endpoints.
- `rendezvous_server.py` — discovery/signaling prototype.

# Rendezvous prototype

A basic register/lookup rendezvous prototype exists. It is discovery/signaling only, not the normal chat transport.

Known flaws:

1. It currently stores the rendezvous connection's observed source endpoint. That source port is ephemeral and is not the peer's P2P listening port. The peer must explicitly advertise its P2P endpoint and later its observed public endpoint.
2. Rendezvous and chat currently collide on `127.0.0.1:9999`; they need separate ports.
3. Registrations never expire. A real version needs TTL/heartbeat/refresh and stale-entry expiry.

# Immediate next milestone — LAN

Do not change encryption, framing, storage, or protocol semantics for LAN testing. Only change the address layer.

### Server

```python
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9999
server.bind(("0.0.0.0", PORT))
```

Print the active LAN IP, for example with:

```python
def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip
```

### Client

```python
host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 9999
client.connect((host, port))
```

### LAN test

1. On the server PC, run `ipconfig` and identify the active Wi-Fi/Ethernet IPv4 address.
2. Start `python server.py 9999`.
3. Verify with `netstat -ano | findstr :9999` that `0.0.0.0:9999` is listening.
4. From the second PC run `Test-NetConnection <SERVER_LAN_IP> -Port 9999`.
5. Only after `TcpTestSucceeded : True`, run `python client.py <SERVER_LAN_IP> 9999`.
6. Verify fingerprints, bidirectional messaging, encrypted history, and restart persistence.

A failed `ping` does not by itself prove TCP is blocked because ICMP may be filtered.

If Windows firewall blocks the connection, investigate the network profile/firewall before changing application code. An explicit rule can be added when appropriate:

```powershell
netsh advfirewall firewall add rule name="p2p-chat-9999" dir=in action=allow protocol=TCP localport=9999
```

### Cleanup before LAN

Fix the client storage-key typo from `client_storage_key.bon` to `client_storage_key.bin`, and standardize the database name to `client_history.db`.

# Internet P2P roadmap

```text
LAN
 ↓
peer.py refactor
 ↓
working rendezvous service
 ↓
public endpoint discovery
 ↓
STUN
 ↓
TCP direct-connection experiment
 ↓
measure result
 ↓
direct P2P if possible
 ↓
relay fallback
```

Do not jump directly to Internet debugging before LAN works.

# NAT traversal

The intended experiment is:

```text
STUN discovery
 ↓
learn public-facing endpoint
 ↓
simultaneous TCP connection attempt
 ↓
measure result
```

TCP hole punching is not guaranteed on modern networks, especially with symmetric NAT, CGNAT, restrictive firewalls, or mobile networks. A failed experiment is still a valid engineering result if the failure is measured, explained, and documented.

V1 requires one real NAT traversal attempt and an explicit fallback strategy, not universal NAT support.

# Security hardening

## Maximum message size

Current `recv_message()` trusts the 4-byte length. A malicious peer could declare an enormous frame and cause dangerous memory/accumulation behavior. Add `MAX_MESSAGE_SIZE` as the first hardening task once remotely reachable.

## Connection state

Today, a receive thread can detect EOF while the send loop continues accepting input, eventually producing errors such as `BrokenPipeError`. A connection state machine should coordinate both sides.

## Socket timeouts

Blocking sockets can hang forever on half-dead connections. Later versions should consider timeouts and/or heartbeats.

## Crypto/decode errors

Malformed input can cause `CryptoError` or `UnicodeDecodeError`. These should be handled without silently killing the receive thread.

## Replay protection

The current protocol has no explicit replay-protection mechanism.

# Security model and limitations

This project does **not** claim Signal-level security.

- **No forward secrecy:** persistent long-term transport keys mean later key compromise may expose recorded traffic. A Signal-style ratchet is out of scope for V1.
- **Local key files are not encrypted at rest:** future versions could use OS-backed credential/key storage.
- **Manual fingerprint verification:** security depends on the user verifying the fingerprint correctly.
- **No professional audit.**
- **Metadata remains visible:** network endpoints, timing, and traffic patterns can leak information.
- **Machine compromise is out of scope.**

Do not use the current project for sensitive real-world communications.

# V1 definition of done

- [x] TCP communication
- [x] TCP framing
- [x] Threaded send/receive
- [x] Encrypted transport
- [x] Persistent cryptographic identity
- [x] Fingerprint verification
- [x] SQLite message history
- [x] Encrypted local history
- [x] Restart persistence
- [ ] LAN communication between two physical machines
- [ ] Unified `peer.py` architecture
- [ ] Working rendezvous service
- [ ] One real NAT traversal experiment
- [ ] Documented NAT result
- [ ] Relay fallback design/prototype
- [ ] Connection state handling
- [ ] Framing/protocol/storage automated tests
- [ ] Threat model
- [ ] Final README
- [ ] Short terminal demo

The goal is to ship a strong 80% project rather than endlessly chase an imaginary 95%. Hardening and additional testing can continue after V1.

# Threat model

### Intended protections

- Passive network observers should not read message plaintext.
- Peers have persistent cryptographic identities.
- Users can manually verify peer identity using fingerprints.
- SQLite history does not contain plaintext messages.
- IP changes do not redefine peer identity.

### Not currently protected against

- Compromise of a peer's machine.
- Theft of local key files.
- Long-term key compromise with recorded traffic.
- Malicious rendezvous-server behavior.
- Traffic analysis and metadata leakage.
- Sophisticated active attacks beyond the current authentication model.
- Universal NAT traversal.
- Implementation vulnerabilities not yet discovered.

# Testing strategy

### Framing

Test empty/small/large messages, fragmented reads, multiple messages, invalid lengths, and oversized frames.

### Storage

Test save/load, multiple peers, direction, timestamps, ciphertext-at-rest, and incorrect storage keys.

### Crypto

Test successful encryption/decryption, wrong keys, persistent identity, and fingerprint stability.

### Integration

```text
connect
 ↓
key exchange
 ↓
fingerprint verification
 ↓
encrypted message
 ↓
store message
 ↓
restart
 ↓
load history
```

# Demo story

The final demonstration should prove the system rather than merely show code:

1. Start peer A.
2. Start peer B.
3. Establish a connection.
4. Verify fingerprints.
5. Send messages both ways.
6. Close the chat.
7. Restart it.
8. Verify the same identity.
9. Show previous encrypted history.
10. Demonstrate two physical machines.
11. Demonstrate rendezvous discovery.
12. Show the direct P2P attempt.
13. Explain relay fallback.

The strongest simple visual milestone is:

```text
Close chat
 ↓
Reopen chat
 ↓
Verify same fingerprint
 ↓
Previous encrypted history appears
```

# Project positioning

### Full description

> A peer-to-peer encrypted messaging system built from Python TCP sockets, implementing custom message framing, persistent cryptographic identities, fingerprint-based peer authentication, encrypted local conversation history, peer discovery, and NAT-aware Internet connectivity.

### Short description

> An educational P2P encrypted messaging system built from raw Python networking primitives, with authenticated peer identities, encrypted transport, encrypted local storage, peer discovery, and NAT traversal.

The project should emphasize implemented engineering rather than simply naming libraries. WebRTC can provide genuine P2P communication, but this project is valuable because the lower networking layers are implemented and understood directly.

# Build-in-public strategy

Use proof-first posts and short terminal recordings rather than generic progress updates.

Strong milestones include:

```text
TCP works
 ↓
TCP framing
 ↓
Encryption
 ↓
Fingerprint verification
 ↓
Persistent identity
 ↓
Encrypted persistent history
 ↓
Two physical machines
 ↓
Cross-network P2P
```

The final repository should include a clean README, architecture diagram, threat model, limitations, testing results, NAT experiment results, demo video, and technical write-up.

# Blog plan — after V1

A blog is worth writing **after the project is actually finished**. The story is stronger than "I built a chat app in Python."

Possible titles:

- **I Built a P2P Encrypted Chat From Raw Python Sockets**
- **What Actually Happens When You Build P2P Messaging From Scratch**

Suggested structure:

1. Why build it instead of using WebRTC/PeerJS?
2. Starting with TCP.
3. Why TCP needs application-level framing.
4. Making send/receive concurrent.
5. Adding public-key encryption and persistent identity.
6. Encryption vs authentication: fingerprints.
7. Encrypted persistent history with SQLite.
8. Moving from localhost to two physical machines.
9. Building peer discovery with a rendezvous server.
10. Attempting real Internet P2P with STUN and TCP traversal.
11. Why direct P2P fails and where relays fit.
12. Security reality check and limitations.
13. What the project taught about networking, protocols, and security.

The blog should document failures honestly. If NAT traversal fails, that result is part of the engineering story rather than something to hide.

# Current status

| Component | Status |
|---|---|
| TCP fundamentals | DONE |
| TCP framing | DONE |
| Threaded communication | DONE |
| PyNaCl encryption | DONE |
| Persistent identity | DONE |
| Fingerprint authentication | DONE |
| SQLite history | DONE |
| SecretBox storage | DONE |
| Restart persistence | DONE |
| Rendezvous prototype | DONE / NEEDS REDESIGN |
| LAN | NEXT |
| Unified `peer.py` | TODO |
| Production-style rendezvous | TODO |
| Internet connectivity | TODO |
| NAT traversal | TODO |
| Relay fallback | TODO |
| Connection state | TODO |
| Security hardening | TODO |
| Automated tests | PARTIAL |
| Threat model | TODO |
| Final README | TODO |
| Demo | TODO |
| Technical blog | AFTER V1 |

# Engineering principle

> **Understand the layer before abstracting it away.**

The point is not to reinvent production-grade messaging software. The point is to understand what TCP actually gives you, what it does not give you, how applications create protocols, how cryptographic identity works, how persistence changes application design, how peers discover each other, why NAT makes P2P difficult, where relays become necessary, and what security guarantees the implementation actually provides.
