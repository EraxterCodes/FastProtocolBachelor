# 🏃🏽 FASTProtocol

_Fair Auctions via Secret Transactions_
The best Bachelor since EMBA's Bachelor
- [🏃🏽 FASTProtocol](#-fastprotocol)
  - [TODO:](#todo)
  - [Security Concerns:](#security-concerns)
  - [Implementation steps](#implementation-steps)
    - [Implementation steps for Off-Chain-Messaging:](#implementation-steps-for-off-chain-messaging)
    - [Bid decomposition](#bid-decomposition)
    - [Publicly Verifiable Secret Sharing (Fig 12, phase F of Off-Chain Messaging)](#publicly-verifiable-secret-sharing-fig-12-phase-f-of-off-chain-messaging)
    - [VetoPhase](#vetophase)


## TODO:
- [x] Get library for P2P
- [x] P2P network with reliable messaging
- [x] Find library for Pedersen commitments (ECPy) - Elliptic curve implementation works!
- [ ] Working Veto
  - [ ]  NIZK in Veto
  - [ ]  Toggle for first or second price auction
- [ ]  Paper
- [ ] using ERC20 / UTXO 
  - [ ] Class for UTXO model
- [ ] GUI

## Security Concerns:
Currently it is possible to listen on others connection like showcased below: p1 is somehow getting p2's bid
![Listen-on-others-connections](/img/Listen-on-others-connection.png)


## Implementation steps

### Implementation steps for Off-Chain-Messaging:
![pki](/img/pki.png)
![off-chain message exchange](/img/off-chain_message_exchange_protocol.png)
Establish Peer-to-Peer network among participants, to allow messages to be exchanged off-chain.

The P2P network uses a modified version of this repo [Macsnoeren Github python-p2p-network](https://github.com/macsnoeren/python-p2p-network). The repository gives a *Node* and a *NodeConnection* which are extended in the *FastNode* and *FastNodeConnection* classes. Changes to these classes are as follow:
**FastNode**:
* Socket timeouts are set to None, so a socket will never time out.
* Fields:
    * clients = A list of clients connected to the node
    * messages = A list of all received messages
  
**FastNodeConnection**:
* Socket timeouts are set to None.
* The thread initializer (run method) sets the field *self.message* to the last message received. *Another implementation option is to save computation and thread overhead would be to stop receiving once a message has been received.*
* Fields:
  * message = The messages that this node connection wants to send
* Methods:
  * get_node_message() = A method that returns the message that is sent.
  * reset_node_message() = Sets the message to an empty string


Initially all nodes connect to a *BroadcastNode* and exchange ID'. The broadcastnode waits until is has made all connections. Afterwards the it sends a message to all nodes with all node and ports connected to the broadcastnode.

Each clientnode extends the *FastNode* class. When instantiating a client a new thread is created and started, such that the client node can accept incoming connections. socket.accept() is a blocker, for this reason it has to run in a thread.

The client connects to the broadcastnode, exchanges ID's and then sends the client node's info (host, port). Then the node waits until it receives a message from the broadcastnode, containing the info for the other nodes, afterwards a connection is made between the client node and the other nodes. The broadcastnode is now useless and therefore disconnected from the client node, making the application entirely P2P.

When all nodes are connected, the signature exchange is started with n rounds.

The implementation uses the python library ECDSA (Elliptic Curve Digital Signature Algorithm) to create a public and private key (Signing key + Verifying key). The signature sharing algorithm goes through n+1 number of rounds. For each round a message and a signed message is send to the other nodes.
****
### Bid decomposition
![setup-phase bid decomposition](/img/setup-phase.png)

### Publicly Verifiable Secret Sharing (Fig 12, phase F of Off-Chain Messaging)
![Publicly Verifiable Secret Sharing](/img/pvss.png)

### VetoPhase
![Veto](/img/VetoPhase.png)
