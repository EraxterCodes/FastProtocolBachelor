# 🏃🏽 FASTProtocol

_Fair Auctions via Secret Transactions_
The best Bachelor since EMBA's Bachelor
- [🏃🏽 FASTProtocol](#-fastprotocol)
  - [TODO:](#todo)
  - [Security Concerns:](#security-concerns)
  - [Implementation steps](#implementation-steps)
    - [Implementation steps for Off-Chain-Messaging:](#implementation-steps-for-off-chain-messaging)
    - [Setup Phase](#setup-phase)
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
### Setup Phase
![setup-phase bid decomposition](/img/setup-phase.png)

For step 3 in stage 1 of the setup phase, each node has to calculate all the Y's for themselves and then broadcast them. 
For a client to calculate the Y for each bid commitment, it has to take the product of all the X's (until the index of the client in the client list) and divide it with the rest of the X's.
For the example the bid commitment will not be shown, but rather just an index:
```math
P_1 = [1, 2, 3] \\
P_2 = [4, 5, 6] \\
P_3 = [7, 8, 9] \\
```
Then the calculation has to be: *(First index is party and second is the bid. I.e. P_2,_2 = 5 (If the party is the first or last node, there will not be a product of any numbers, but instead just a 1 to avoid issues.))*
```math
Y_1,_1 = [] / [P_2,_1 * P_3,_1] = 1 / (4*7) \approx 0,0357 \\
Y_2,_1 = P_1,_1 / P_3,_1 = 1 / 7 \approx 0,1428 \\
Y_3,_1 = [P_1,_1 * P_2,_1] / [] = (1*4) / 1 \approx 4 \\~\\
Y_1,_2 = [] / [P_2,_2 * P_3,_2] = 1 / (5*8) \approx 0,025 \\
Y_2,_2 = P_1,_2 / P_3,_2 = 2/8 \approx 0,25 \\
Y_3,_2 = [P_1,_2 * P_2,_2] / [] = (2*5) / 1 \approx 10 \\~\\
Y_1,_3 = [] / [P_2,_3 * P_3,_3] = 1 / (6*9) \approx 0,0185 \\
Y_2,_3 = P_1,_3 / P_3,_3 = 3 / 9 \approx 0,3333 \\
Y_3,_3 = [P_1,_3 * P_2,_3] / [] = (2*6) / 1 \approx 12 \\
```
Note that this is a simplified example. The actual prototype uses groups and elliptic curves with points instead of simple integers.

### Publicly Verifiable Secret Sharing (Fig 12, phase F of Off-Chain Messaging)
![Publicly Verifiable Secret Sharing](/img/pvss.png)

### VetoPhase
![Veto](/img/VetoPhase.png)
