# 🏃🏽 FASTProtocol

## How to launch
First, ensure you have the correct packages installed by running `python setup.py install`. When all dependencies are installed, run `python main.py` and then the protocol will start. From here, follow the steps given in the terminal, to run the specific protocol type.

<hline>


_Fair Auctions via Secret Transactions_
The best Bachelor since EMBA's Bachelor
- [🏃🏽 FASTProtocol](#-fastprotocol)
  - [TODO:](#todo)
  - [Implementation steps](#implementation-steps)
    - [Implementation steps for Off-Chain-Messaging:](#implementation-steps-for-off-chain-messaging)
    - [Publicly Verifiable Secret Sharing (Fig 12, phase F of Off-Chain Messaging)](#publicly-verifiable-secret-sharing-fig-12-phase-f-of-off-chain-messaging)
  - [FPA](#fpa)
    - [Setup Phase (Stage 1)](#setup-phase-stage-1)
    - [VetoPhase (Stage 2, 3)](#vetophase-stage-2-3)
    - [Stage 4, output](#stage-4-output)
    - [Recovery](#recovery)
    - [Smart Contract](#smart-contract)
    - [Multiprocessing / Multithreads for NIZK](#multiprocessing--multithreads-for-nizk)
  - [Things we miss:](#things-we-miss)
    - [(FIXED) Calculate commit for bid and send it](#fixed-calculate-commit-for-bid-and-send-it)
    - [(FIXED) Fix, such that client only sends to broadcast node](#fixed-fix-such-that-client-only-sends-to-broadcast-node)
    - [Send commits to nodes in fragments](#send-commits-to-nodes-in-fragments)


## TODO:
- [x] Get library for P2P
- [x] P2P network with reliable messaging
- [x] Find library for Pedersen commitments (ECPy) - Elliptic curve implementation works!
- [x] FPA
  - [x] Stage 1
  - [x] Stage 2
    - [x] Veto, Before first veto
  - [x] Stage 3
    - [x] NIZK
    - [x] Veto, after first veto
  - [x] Stage 4
- [ ] NIZK multiprocessing / multithreads
- [ ]  Paper
- [ ] using ERC20 / UTXO 
  - [ ] Class for UTXO model
- [ ] GUI

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

### Publicly Verifiable Secret Sharing (Fig 12, phase F of Off-Chain Messaging)
![Publicly Verifiable Secret Sharing](/img/pvss.png)

## FPA
### Setup Phase (Stage 1)
![setup-phase bid decomposition](/img/setup-phase.png)

For step 3 in stage 1 of the setup phase, each node has to calculate all the Y's for themselves and then broadcast them. 
For a client to calculate the Y for each bid commitment, it has to take the product of all the X's (until the index of the client in the client list) and divide it with the rest of the X's.
For the example the bid commitment will not be shown, but rather just an index:
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large P_1 = [1, 2, 3]"></div>
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large P_2 = [4, 5, 6]"></div>
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large P_3 = [7, 8, 9]"></div>

Then the calculation has to be: *(First index is party and second is the bid. I.e. P_2,_2 = 5 (If the party is the first or last node, there will not be a product of any numbers, but instead just a 1 to avoid issues.))*
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large Y_1,_1 = [] / [P_2,_1 * P_3,_1] = 1 / 4*7 \approx 0,0357"></div>
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large Y_2,_1 = P_1,_1 / P_3,_1 = 1 / 7 \approx 0,1428"></div>
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large Y_3,_1 = [P_1,_1 * P_2,_1] / [] = (1*4) / 1 \approx 4"></div>
<br>
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large Y_1,_2 = [] / [P_2,_2 * P_3,_2] = 1 / (5*8) \approx 0,025"></div>
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large Y_2,_2 = P_1,_2 / P_3,_2 = 2/8 \approx 0,25"></div>
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large Y_3,_2 = [P_1,_2 * P_2,_2] / [] = (2*5) / 1 \approx 10"></div>
<br>
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large Y_1,_3 = [] / [P_2,_3 * P_3,_3] = 1 / (6*9) \approx 0,0185"></div>
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large Y_2,_3 = P_1,_3 / P_3,_3 = 3 / 9 \approx 0,3333"></div>
<div align="center"><img src="https://render.githubusercontent.com/render/math?math=\large Y_3,_3 = [P_1,_3 * P_2,_3] / [] = (2*6) / 1 \approx 12"></div>

Note that this is a simplified example. The actual prototype uses groups and elliptic curves with points instead of simple integers.

We're still missing this part:
![Commit verification](/img/verify_commit.png)
(Essentially it's just the commit to the bid, which also has to be sent to the smart contract.)

### VetoPhase (Stage 2, 3)
![Veto](/img/VetoPhase.png)

When generating the NIZK, there's a bit of headscratching to do. Two NIZK's are created, one for before the first veto and one for after the first veto.
![Nizk bfv](/img/nizk1.png)
I assume that two proofs has to be done for this. There needs to be a proof of either <img src="https://render.githubusercontent.com/render/math?math=F_1"> or <img src="https://render.githubusercontent.com/render/math?math=F_2"> depending on what bit to round r you have. If the bit is 0 then you make a proof for <img src="https://render.githubusercontent.com/render/math?math=F_1"> and if the bit it 1 then you make a proof of <img src="https://render.githubusercontent.com/render/math?math=F_2">. The beautiful part is that the other part doesn't know what you've prooven, just that you've correctly calculated it.
For the equation we have a constant <img src="https://render.githubusercontent.com/render/math?math=\alpha">, which is either 1 or 2 (As mentioned in step 4). <img src="https://render.githubusercontent.com/render/math?math=\alpha"> denotes what F we want to calculate. Furthermore there's also the variable <img src="https://render.githubusercontent.com/render/math?math=i">. <img src="https://render.githubusercontent.com/render/math?math=i"> is mentioned both as the party, to sample <img src="https://render.githubusercontent.com/render/math?math=v"> and to sample <img src="https://render.githubusercontent.com/render/math?math=w">. However, when we want to put <img src="https://render.githubusercontent.com/render/math?math=i"> in relation to <img src="https://render.githubusercontent.com/render/math?math=\alpha">, we only look at what <img src="https://render.githubusercontent.com/render/math?math=\gamma"> that needs to be calculated. So if we want to do proof for <img src="https://render.githubusercontent.com/render/math?math=\alpha"> = 1, then <img src="https://render.githubusercontent.com/render/math?math=\gamma_1 = H - (w_1 + w_2) (mod q)"> and <img src="https://render.githubusercontent.com/render/math?math=\gamma_2 = w_i \approx w_2">. If <img src="https://render.githubusercontent.com/render/math?math=\alpha \neq i"> then <img src="https://render.githubusercontent.com/render/math?math=\gamma_1 = w_1"> and <img src="https://render.githubusercontent.com/render/math?math=\gamma_2 = H - (w_1+w_2) (mod q)">.

Let's start from **step 1** (But in human language).
We have to prove <img src="https://render.githubusercontent.com/render/math?math=F_1, F_2">. 
<img src="https://render.githubusercontent.com/render/math?math=F_1 =">We start by proving <img src="https://render.githubusercontent.com/render/math?math=\alpha = 1">, which means calculating <img src="https://render.githubusercontent.com/render/math?math=F_1">. <img src="https://render.githubusercontent.com/render/math?math=V = (v_1, v_2, v_3, v_4)"> are created by sampling random elements from the field of <img src="https://render.githubusercontent.com/render/math?math=\mathbb{Z}_q"> (Meaning <img src="https://render.githubusercontent.com/render/math?math=v_1 ... v_4"> are random elements from <img src="https://render.githubusercontent.com/render/math?math=1 ... q-1">). Then <img src="https://render.githubusercontent.com/render/math?math=w = (w_1, w_2)"> is created. These elements are also sampled at random from the field of <img src="https://render.githubusercontent.com/render/math?math=\mathbb{Z}_q">. However, since <img src="https://render.githubusercontent.com/render/math?math=\alpha = 1">, then it's only <img src="https://render.githubusercontent.com/render/math?math=w_2"> that's sampled at random and <img src="https://render.githubusercontent.com/render/math?math=w_1 = 0">. Now that both values <img src="https://render.githubusercontent.com/render/math?math=V"> and <img src="https://render.githubusercontent.com/render/math?math=w"> are selected, <img src="https://render.githubusercontent.com/render/math?math=t_1 ... t_5"> can be calculated, using the public values <img src="https://render.githubusercontent.com/render/math?math=c, h, v, g, X, Y"> (In section 2.2.NIZK For Stage 2, the paper says that <img src="https://render.githubusercontent.com/render/math?math=v, c, X, g, Y"> are public, but i assume <img src="https://render.githubusercontent.com/render/math?math=h"> is also public, as it's a shared value for the pedersen commitments).
In **step 2**, <img src="https://render.githubusercontent.com/render/math?math=H"> is calculated, which is all of the values added together (I think, Bernardo plz respond) modulo q. 
From here, we can go to **step 3**, where <img src="https://render.githubusercontent.com/render/math?math=\Gamma = (\gamma_1, \gamma_2)"> is calculated. For this step we need to use <img src="https://render.githubusercontent.com/render/math?math=\alpha"> again. Since <img src="https://render.githubusercontent.com/render/math?math=\alpha = 1">, then for <img src="https://render.githubusercontent.com/render/math?math=\gamma_1"> we calculate <img src="https://render.githubusercontent.com/render/math?math=\gamma_1 = H - (w_1 + w_2) (mod q)"> and for <img src="https://render.githubusercontent.com/render/math?math=\gamma_2"> is simply <img src="https://render.githubusercontent.com/render/math?math=\gamma_2 = w_2">.
In **step 4**, <img src="https://render.githubusercontent.com/render/math?math=R = (r_1, r_2, r_3, r_4, r_5)"> is calculated. Again, since we want to proove <img src="https://render.githubusercontent.com/render/math?math=F_1">, then <img src="https://render.githubusercontent.com/render/math?math=\aplha = 1"> and then we have the tuple <img src="https://render.githubusercontent.com/render/math?math=(x_1, x_2, x_3, x_4) = (r_i_r, x_i_r, 0, 0)">. All values of <img src="https://render.githubusercontent.com/render/math?math=R"> has to be calculated in order to check the validity of the proof.

When calculating <img src="https://render.githubusercontent.com/render/math?math=F_2">, then <img src="https://render.githubusercontent.com/render/math?math=\alpha"> is then also set to 2.
For **step 1**, the same approach is done again, however when choosing <img src="https://render.githubusercontent.com/render/math?math=w">, then <img src="https://render.githubusercontent.com/render/math?math=w_1"> is randomly sampled and <img src="https://render.githubusercontent.com/render/math?math=w_2"> is 0.
**Step 2** is also the same as in <img src="https://render.githubusercontent.com/render/math?math=F_1">.
**Step 3** has to be switched around, such that <img src="https://render.githubusercontent.com/render/math?math=\gamma_1 = w_1 ="> random sample of <img src="https://render.githubusercontent.com/render/math?math=\mathbb{Z}_q"> and <img src="https://render.githubusercontent.com/render/math?math=\gamma_2 = H - (w_1 + w_2) (mod q)">.
**Step 4** is also the same, however since <img src="https://render.githubusercontent.com/render/math?math=\alpha = 2"> then we have <img src="https://render.githubusercontent.com/render/math?math=(x_1, x_2, x_3, x_4) = (0, 0, r_i_r, \hat{r}_i_r)">. Then we have everything to proove we have calculated <img src="https://render.githubusercontent.com/render/math?math=v"> correctly.

### Stage 4, output
![Stage4](/img/stage4.png)

### Recovery
Comittee is needed for this stage
![Recovery](/img/recovery.png)

### Smart Contract
*Pseudo code*
The smart contract takes care of punishing cheaters, as well as controlling the currency. We propose that a person that wants to sell an item, instantiate a smart contract with following parameters and functions:
```solidity
struct Client {
  address public publickey;
  uint256 bid;
  string host;
  uint256 port;
}

struct Auction {
  uint256 price;
  address seller;
  address buyer;
  uint256 timestamp;
  bool isSold;
  Client[] clients;
}

constructor() public {
  Auction auction = Auction(0, msg.sender, "0x00", block.timestamp, false, []);
}
```

Once a person has instantiated the smart contract, other parties can join the auction through the address of the contract, calling a method ```joinAuction``` with the following parameters:
```solidity
function joinAuction(uint256 _bid, string _host, uint256 port) public payable {
  Client client = Client(msg.sender, _bid, _host, port);
  auction.clients.push(client)
}
```
And then the Auction object should append the client to the array of clients. Finally, once the seller (owner of the contract) is happy with the amount of people that has joined, he can call the method ```startAuction```, which in tern starts the auction and the therefore the protocol:
```solidity
function startAuction() public returns (bool) {
  if(auction.seller == msg.sender) {
    -- start the auction -- 

    return true;
  } else {
    return false;
  }
}
```

### Multiprocessing / Multithreads for NIZK
Currently when runing the protocol the NIZK calulation grows O(n) (linear) when adding a new node. Calculating the nizk is done sequentially, which can take a long time. We propose adding multiprocessing in pools (Or multi threads) to calculate the NIZK in parallel.

## Things we miss:
### (FIXED) Calculate commit for bid and send it
We're still missing this part:
![Commit verification](/img/verify_commit.png)
(Essentially it's just the commit to the bid, which also has to be sent to the smart contract.)

### (FIXED) Fix, such that client only sends to broadcast node
Currently it is possible to listen on others connection like showcased below: p1 is somehow getting p2's bid
![Listen-on-others-connections](/img/Listen-on-others-connection.png)

### Send commits to nodes in fragments
Currently we're sending the commits to the nodes as one big array. However, we often get (Especially when running many nodes) errors that all X's and Y's are not send correctly. We believe this is because the messages are too big to be send and then never arrive, or arrive in broken fragments.

A fix to this would be calculating the commits in fragments, and then sending them to the nodes. I.e. calculating 1/4 or 1/2 of the commitments and then sending them. Then the node receives and unpacks and then repeat until all commits are received.
