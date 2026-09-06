# P2P Encrypted Chat

An educational **peer-to-peer encrypted messaging system built from
Python sockets and cryptographic primitives**, with persistent
cryptographic identities, fingerprint-based peer authentication,
encrypted local chat history, peer discovery, and eventually
Internet/NAT-aware connectivity.

The project is intentionally built from lower-level networking
primitives rather than hiding the networking behind WebRTC, PeerJS, or a
chat framework.

> **Security note:** This is an educational implementation, not a
> production-secure messenger and should not be compared with
> Signal-level security guarantees.

------------------------------------------------------------------------

## 1. Project Goal

The original goal is not a localhost chat application.

The final goal is:

``` text
Person A's computer
        ↕
     Internet
        ↕
Person B's computer
```

with the actual chat traffic flowing directly between peers whenever
network conditions allow.

The project should demonstrate understanding and implementation of:

-   TCP networking
-   message framing
-   authenticated encrypted communication
-   persistent cryptographic identity
-   peer fingerprint verification
-   encrypted local persistence
-   peer discovery / rendezvous
-   LAN networking
-   public vs private addressing
-   NAT and firewall behavior
-   NAT traversal
-   P2P connection management

------------------------------------------------------------------------

# 2. Current Architecture

## Network communication

``` text
User
  ↓
Chat
  ↓
PyNaCl Box
  ↓
Message framing
  ↓
TCP sockets
  ↓
Peer
```

## Local storage

``` text
Message
  ↓
SecretBox
  ↓
SQLite
```

The two encryption layers have different purposes.

### `Box`

Protects messages **while travelling between peers**.

### `SecretBox`

Protects messages **stored locally on disk**.

They use separate persistent keys.

------------------------------------------------------------------------

# 3. Current Project Files

Current working files include:

``` text
client.py
server.py
protocol.py
identity.py
storage.py
crypto_test.py

rendezvous_server.py
rendezvous_test.py

client_key.bin
server_key.bin
client_storage_key.bin
server_storage_key.bin

client_history.db
server_history.db
```

The exact rendezvous filenames may currently have longer/generated names
in the working directory, but they represent the rendezvous server and
its test client.

Local/private files:

``` text
*.bin
*.db
```

should not be committed to Git.

------------------------------------------------------------------------

# 4. Completed Milestones

## Milestone 1 --- TCP sockets

### What we built

A basic TCP client/server connection using Python's `socket` module.

Implemented and understood:

-   `socket()`
-   `bind()`
-   `listen()`
-   `accept()`
-   `connect()`
-   `send()`
-   `recv()`
-   `sendall()`

### Why we needed it

TCP provides the reliable byte stream on which the rest of the chat
protocol operates.

### What we chose

Python TCP sockets instead of a networking framework.

### Why

The project is intended to teach the underlying networking concepts
rather than abstract them away.

### Result

The client and server can establish a TCP connection and exchange data.

------------------------------------------------------------------------

## Milestone 2 --- Blocking sockets and threading

### What we built

The chat uses blocking sockets and a separate receiving thread.

Conceptually:

``` text
Main thread
    ↓
read user input
    ↓
encrypt
    ↓
send


Receive thread
    ↓
recv
    ↓
decrypt
    ↓
display
```

### Why we needed it

A blocking `recv()` would otherwise prevent the user from typing while
waiting for an incoming message.

### Result

Both sides can send and receive messages simultaneously.

------------------------------------------------------------------------

## Milestone 3 --- TCP message framing

### What we built

A custom length-prefixed message protocol:

``` text
[4-byte length][message bytes]
```

Implemented in `protocol.py`:

``` python
send_message(sock, data)
recv_message(sock)
```

The length is encoded using:

``` python
struct.pack("!I", length)
```

and decoded using:

``` python
struct.unpack("!I", header)
```

### Why we needed it

TCP is a byte stream. It does not preserve application-level message
boundaries.

One call to `send()` does not necessarily correspond to one call to
`recv()`.

### Result

The application can reliably reconstruct complete messages from the TCP
stream.

------------------------------------------------------------------------

## Milestone 4 --- Public/private key cryptography

### What we built

Each side generates a persistent PyNaCl public/private key pair.

``` text
Private key
    ↓
Public key
```

The current implementation uses PyNaCl's `Box`.

### Why we needed it

We need encrypted communication between peers without sharing a single
symmetric key beforehand.

### Result

Each peer can derive a secure encrypted communication context using:

``` python
Box(private_key, peer_public_key)
```

------------------------------------------------------------------------

## Milestone 5 --- Public-key exchange handshake

### What we built

A simple asymmetric handshake.

Client:

``` text
Client → Client public key
Client ← Server public key
```

Server:

``` text
Server ← Client public key
Server → Server public key
```

The order was deliberately chosen so that both sides do not wait for the
other indefinitely.

### Result

Both peers have the other peer's public key and can construct their
`Box`.

------------------------------------------------------------------------

## Milestone 6 --- Persistent cryptographic identity

### What we built

`identity.py` contains:

``` python
load_or_create_key(filename)
```

If the key file exists:

``` text
read existing private key
```

Otherwise:

``` text
generate private key
save it
```

Current identity files:

``` text
client_key.bin
server_key.bin
```

### Why we needed it

If a new key were generated every time the application started, the peer
would have a different identity on every run.

### Result

A peer's cryptographic identity persists across restarts.

------------------------------------------------------------------------

## Milestone 7 --- Fingerprint verification

### What we built

The peer's public key is hashed using SHA-256:

``` python
hashlib.sha256(public_key_bytes).hexdigest()
```

The hash is displayed in grouped form:

``` text
ABCD:1234:5678:....
```

The user manually confirms the fingerprint.

### Why we needed it

Encryption alone does not solve the problem of knowing **who** is on the
other end.

Fingerprint verification provides a simple manual authentication
mechanism.

### Important design choice

The peer's fingerprint is used as its identity rather than its IP
address.

------------------------------------------------------------------------

## Milestone 8 --- SQLite chat history

### What we built

`storage.py` creates a SQLite database containing:

``` text
id
fingerprint
direction
text
timestamp
```

Messages are associated with the peer fingerprint.

### Why we needed it

Chat history should survive application restarts.

### Important design choice

History is keyed by:

``` text
peer fingerprint
```

rather than:

``` text
IP address
```

because IP addresses can change while cryptographic identity should
remain stable.

------------------------------------------------------------------------

## Milestone 9 --- Encrypted local storage

### What we built

A separate persistent `SecretBox` key is generated and stored locally.

Current storage keys:

``` text
client_storage_key.bin
server_storage_key.bin
```

Saving:

``` text
Plaintext message
      ↓
SecretBox.encrypt()
      ↓
SQLite BLOB
```

Loading:

``` text
SQLite BLOB
      ↓
SecretBox.decrypt()
      ↓
Plaintext message
```

### Why we needed it

Encrypting network traffic does not protect messages once they are
written to disk.

### Result

The local SQLite database does not contain plaintext chat messages.

------------------------------------------------------------------------

## Milestone 10 --- Persistent restart loop

### What we proved

The complete local/test loop works:

``` text
TCP
 ↓
framing
 ↓
encrypted communication
 ↓
persistent identity
 ↓
fingerprint verification
 ↓
encrypted SQLite history
 ↓
application restart
 ↓
history loads again
```

This was an important transition from a networking experiment into an
actual persistent application.

------------------------------------------------------------------------

## Milestone 11 --- Rendezvous server prototype

### What we built

A basic rendezvous server prototype.

It supports requests conceptually like:

``` json
{
    "type": "register",
    "id": "aadarsh"
}
```

and:

``` json
{
    "type": "lookup",
    "id": "aadarsh"
}
```

The server maintains an in-memory peer registry.

### Why we need it

A real P2P system still often needs a server for
**discovery/signaling**, even though the server does not carry the
actual chat messages.

Target architecture:

``` text
              Rendezvous Server
                /          \
          discovery       discovery
              ↓              ↓
           Peer A  ←──────→ Peer B
                   chat
```

### Current status

This is only a prototype and is **not yet a correct Internet P2P
discovery system**.

The current implementation stores the TCP address observed from the
rendezvous connection:

``` python
peers[peer_id] = address
```

That address is the endpoint of the peer's rendezvous connection, not
necessarily the endpoint where the peer accepts P2P chat connections.

This must be redesigned before using rendezvous for real peer
connectivity.

------------------------------------------------------------------------

# 5. Current Message Flow

## Network

``` text
"text"
   ↓
.encode()
   ↓
Box.encrypt()
   ↓
send_message()
   ↓
[4-byte length][ciphertext]
   ↓
TCP
   ↓
recv_message()
   ↓
Box.decrypt()
   ↓
.decode()
   ↓
"text"
```

## Database

``` text
"text"
   ↓
SecretBox.encrypt()
   ↓
SQLite BLOB
```

and:

``` text
SQLite BLOB
   ↓
SecretBox.decrypt()
   ↓
.decode()
   ↓
"text"
```

------------------------------------------------------------------------

# 6. What Is Left

## Phase 1 --- LAN connectivity

### Status: NEXT

Move from:

``` text
127.0.0.1
```

to actual LAN communication.

Target:

``` text
Computer A
192.168.x.x
      ↕
    LAN
      ↕
Computer B
192.168.x.x
```

Learn and test:

-   private IPv4 addresses
-   listening interfaces
-   ports
-   LAN routing
-   Windows firewall
-   TCP reachability
-   connection diagnostics

### Success condition

Two physical computers can run the current chat and communicate over the
same LAN.

------------------------------------------------------------------------

# Phase 2 --- Refactor client/server into a peer

### Status: PLANNED

Current architecture:

``` text
server.py ←→ client.py
```

Target:

``` text
peer.py
```

Every peer should be able to:

``` text
listen
accept
connect
send
receive
```

Conceptually:

``` text
             Peer
        ┌─────────────┐
        │ listen      │
        │ accept      │
        │ connect     │
        │ send        │
        │ receive     │
        └─────────────┘
```

This removes the conceptual distinction between permanent "server" and
"client".

------------------------------------------------------------------------

# Phase 3 --- Real peer discovery / rendezvous

### Status: PROTOTYPE EXISTS

Build a proper rendezvous mechanism.

The rendezvous service should handle things such as:

``` text
Peer ID
Public key / fingerprint
Listening information
Peer availability
Connection metadata
```

It should be used for:

``` text
discovery / signaling
```

not:

``` text
chat message transport
```

The actual chat should remain:

``` text
Peer A ←────────→ Peer B
```

------------------------------------------------------------------------

# Phase 4 --- Internet connectivity

### Status: NOT STARTED

Move peers from the same LAN to different networks.

Understand:

``` text
Private IP
    ↓
NAT
    ↓
Router
    ↓
Public Internet
    ↓
Router
    ↓
NAT
    ↓
Private IP
```

Topics:

-   public IP
-   private IP
-   ports
-   inbound connections
-   outbound connections
-   NAT
-   firewall
-   port forwarding
-   why direct TCP connections fail across many home networks

------------------------------------------------------------------------

# Phase 5 --- NAT traversal

### Status: MAJOR REMAINING COMPONENT

Investigate and implement an appropriate connectivity mechanism.

Potential components:

-   STUN
-   endpoint discovery
-   UDP hole punching
-   TCP traversal where applicable
-   rendezvous-assisted connection setup
-   relay fallback if direct connectivity is impossible

The goal is not to pretend every NAT can be defeated.

The goal is to build a system that:

``` text
attempts direct P2P connectivity
        ↓
uses traversal techniques where possible
        ↓
handles failure explicitly
```

------------------------------------------------------------------------

# Phase 6 --- Connection state management

### Status: PLANNED

Introduce an explicit connection lifecycle:

``` text
DISCOVERING
     ↓
KNOWN
     ↓
CONNECTING
     ↓
CONNECTED
     ↓
AUTHENTICATING
     ↓
VERIFIED
     ↓
CHAT
```

Failure paths should be handled explicitly:

``` text
CONNECTING
     ↓
FAILED
     ↓
RETRY / ALTERNATIVE
```

This becomes important once discovery, NAT traversal, and reconnect
logic are introduced.

------------------------------------------------------------------------

# Phase 7 --- Security hardening

### Status: PLANNED

The current cryptographic implementation is a strong educational
foundation, but it is not a complete production security protocol.

Investigate:

-   malformed packets
-   maximum message size
-   nonce handling
-   replay considerations
-   key replacement
-   identity changes
-   connection timeouts
-   peer authentication
-   graceful disconnect
-   concurrent connections
-   error handling
-   key-file protection

Document the threat model and limitations honestly.

------------------------------------------------------------------------

# Phase 8 --- Application polish

### Status: PLANNED

Turn the networking system into a clean usable application.

Potential features:

-   peer identity
-   connection status
-   verified fingerprint
-   send/receive messages
-   persistent history
-   reconnect
-   clear connection errors
-   graceful shutdown

The UI should remain secondary to the networking architecture.

------------------------------------------------------------------------

# Phase 9 --- Testing

### Status: PLANNED

Test at multiple network levels.

## Local

``` text
Peer A ↔ Peer B
```

## LAN

``` text
Computer A ↔ Computer B
```

## Different networks

``` text
Network A ↔ Internet ↔ Network B
```

## Failure cases

Test:

-   peer offline
-   wrong fingerprint
-   wrong public key
-   wrong port
-   firewall blocking connection
-   malformed frame
-   oversized frame
-   connection dropped
-   peer restart
-   identity persistence
-   IP change
-   corrupted storage
-   rendezvous peer not found

------------------------------------------------------------------------

# Phase 10 --- Final documentation

### Status: PLANNED

The final documentation should explain:

``` text
Architecture
Networking model
Message framing
Cryptographic design
Peer identity
Fingerprint authentication
Storage encryption
Peer discovery
NAT traversal
Connection lifecycle
Threat model
Known limitations
Testing
Running the project
```

The documentation should remain concise and technical.

For each milestone:

``` text
What we built

Why we needed it

What we chose

Why we chose it

Result
```

Avoid generic tutorial-style explanations and unnecessary fluff.

------------------------------------------------------------------------

# 7. Final Target Architecture

The intended final architecture is:

``` text
                       ┌──────────────────────┐
                       │  Rendezvous Server   │
                       │                      │
                       │  Discovery/Signaling │
                       └──────────┬───────────┘
                                  │
                         connection information
                           ↙              ↘
                          ↓                ↓

                    ┌──────────┐      ┌──────────┐
                    │  Peer A  │◄────►│  Peer B  │
                    │          │      │          │
                    │ listen   │      │ listen   │
                    │ connect  │      │ connect  │
                    └────┬─────┘      └────┬─────┘
                         │                  │
                         └──── P2P TCP ─────┘
                                  │
                           Message framing
                                  │
                             PyNaCl Box
                                  │
                               Chat
                                  │
                           SecretBox
                                  │
                              SQLite
```

The rendezvous server helps peers **find each other**.

It should not become the permanent middleman for chat traffic.

------------------------------------------------------------------------

# 8. Final Project Definition

The finished project should be described as:

> **A peer-to-peer encrypted messaging system built from Python TCP
> sockets, implementing custom message framing, persistent cryptographic
> identities, fingerprint-based peer authentication, encrypted local
> conversation history, peer discovery, and NAT-aware Internet
> connectivity.**

A shorter description:

> **An educational P2P encrypted messaging system built from raw Python
> networking primitives, with authenticated peer identities, encrypted
> transport, encrypted local storage, peer discovery, and NAT
> traversal.**

------------------------------------------------------------------------

# 9. What Makes This Project Different

This is not intended to compete with WebRTC/PeerJS-based chat
applications by having a prettier UI.

The technical goal is to understand and implement the networking layers
underneath a P2P system.

Comparison:

``` text
Typical P2P student project

Application
    ↓
WebRTC / PeerJS
    ↓
Network
```

This project:

``` text
Application
    ↓
Peer management
    ↓
Peer discovery
    ↓
Cryptographic identity
    ↓
PyNaCl encryption
    ↓
Custom message framing
    ↓
TCP sockets
    ↓
IP networking
    ↓
NAT / firewall / traversal
```

The project therefore demonstrates both **application development and
networking fundamentals**.

------------------------------------------------------------------------

# 10. Development Roadmap

Current progression:

``` text
TCP
  ↓
TCP framing
  ↓
Threaded communication
  ↓
Encryption
  ↓
Fingerprint authentication
  ↓
Persistent identity
  ↓
Encrypted local history
  ↓
Restart persistence
  ↓
Rendezvous prototype
  ↓
LAN connectivity              ← NEXT
  ↓
Unified peer.py
  ↓
Real peer discovery
  ↓
Different networks
  ↓
NAT + firewall
  ↓
NAT traversal
  ↓
Connection state/reconnect
  ↓
Security hardening
  ↓
Testing
  ↓
Documentation
  ↓
Polished portfolio project
```

------------------------------------------------------------------------

# 11. Current Immediate Task

**Do not rewrite the entire project yet.**

The immediate milestone is:

> **Make the existing encrypted chat work between two physical computers
> on the same LAN.**

After that:

1.  Refactor the architecture into `peer.py`.
2.  Correctly integrate rendezvous/discovery.
3.  Test peers on different networks.
4.  Study and implement NAT traversal.
5.  Harden the protocol.
6.  Test failure cases.
7.  Polish and document the final system.

------------------------------------------------------------------------

# 12. Project Status

``` text
Foundation                         ████████████████████  DONE

LAN networking                     ░░░░░░░░░░░░░░░░░░░░  NEXT
Peer refactor                      ░░░░░░░░░░░░░░░░░░░░
Rendezvous integration             ████░░░░░░░░░░░░░░░░  PROTOTYPE
Internet connectivity              ░░░░░░░░░░░░░░░░░░░░
NAT traversal                      ░░░░░░░░░░░░░░░░░░░░
Connection state                   ░░░░░░░░░░░░░░░░░░░░
Security hardening                 ░░░░░░░░░░░░░░░░░░░░
Testing                            ░░░░░░░░░░░░░░░░░░░░
Documentation                     ░░░░░░░░░░░░░░░░░░░░
Final polish                       ░░░░░░░░░░░░░░░░░░░░
```

This document is **living project documentation**. New milestones should
be added as the implementation progresses.
