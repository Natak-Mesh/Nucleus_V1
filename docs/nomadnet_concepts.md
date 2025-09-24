Title: Concepts and Terminology
Date: 2023-05-16

# Concepts and Terminology

The following section will briefly introduce various concepts and terms used in the program.

## Peer

A *peer* refers to another Nomad Network client, which will generally be operated by another person. But since Nomad Network is a general LXMF client, it could also be any other LXMF client, program, automated system or machine that can communicate over LXMF.

All peers (and nodes) are identified by their *address* (which is, technically speaking, a Reticulum destination hash). An address consist of 32 hexadecimal characters (16 bytes), and looks like this:

`<e9eafceea9e3664a5c55611c5e8c420a# `

Anyone can choose whatever display name they want, but addresses are always unique, and generated from the unique cryptographic keys of the peer. This is an important point to understand. Since there is not anyone controlling naming or address spaces in Nomad Network, you can easily come across another user with the same display name as you.

Your addresses will always be unique though, and you must always verify that the address you are communicating with is matching the address of the peer you expect to be in the other end.

To make this easier, Nomad Network allows you to mark peers and nodes as either *trusted*, *unknown* or *untrusted*. In this way, you can mark the peers and nodes that you know to be legitimate, and easily spot peers with similar names as unrelated.

## Announces

An *announce* can be sent by any peer or node on the network, which will notify other peers of its existence, and contains the cryptographic keys that allows other peers to communicate with it.

In the **[ Network ]** section of the program, you can monitor announces on the network, initiate conversations with announced peers, and announce your own peer on the network. You can also connect to nodes on the network and browse information shared by them.

## Conversations

Nomad Network uses the term *conversation* to signify both direct peer-to-peer messaging threads, and also discussion threads with an arbitrary number of participants that might change over time.

Both things like discussion forums and chat threads can be encapsulated as conversations in Nomad Network. The user interface will indicate the different characteristics a conversation can take, and also what form of transport encryption was used for messages within.

In the **[ Conversations ]** part of the program you can view and interact with all currently active conversations. You can also edit nickname and trust settings for peers belonging to these conversations here. To edit settings for a peer, select it in the conversation list, and press **Ctrl-E**.

By default, Nomad Network will attempt to deliver messages to a peer directly. This happens by first establishing an encrypted link directly to the peer, and then delivering the message over it.

If the desired peer is not available because it has disconnected from the network, this method will obviously fail. In this case, Nomad Network will attempt to deliver the message to a node, which will store and forward it over the network, for later retrieval by the destination peer. The message is encrypted before being transmitted to the network, and is only readable by the intended recipient.

For propagated delivery to work, one or more nodes must be available on the network. If one or more trusted nodes are available, Nomad Network will automatically select the most suitable node to send the message via, but you can also manually specify what node to use.

To select a node manually, go to the **[ Network ]** part of the program, choose the desired node in the *Known Nodes* list, and select the **< Info # ** button. In the **Node Info** dialog, you can specify the selected node as the default propagation node.

By default, Nomad Network will check in with propagation nodes, and download any available messages every 6 hours. You can change this interval, or disable automatic syncronisation completely, by editing the configuration file.

You can always initiate a sync manually, by pressing **Ctrl-R** in the **[ Conversations ]** part of the program, which will open the syncronisation window.

## Node

A Nomad Network *node* is an instance of the Nomad Network program that has been configured to host information for other peers and help propagate messages and information on the network.

Nodes can host pages (similar to webpages) written in a markup-language called *micron*, as well as make files and other resources available for download for peers on the network. Nodes also form a distributed message store for offline users, and allows messages to be exchanged between peers that are not online at the same time.

If no nodes exist on a network, all peers will still be able to communicate directly peer-to-peer, but both endpoints of a conversation will need to be available at the same time to converse. When nodes exist on the network, messages will be held and syncronised between nodes for deferred delivery if the destination peer is unavailable. Nodes will automatically discover and peer with each other, and handle syncronisation of message stores.

To learn how to host your own node, read the *Hosting a Node* section of this guide.
