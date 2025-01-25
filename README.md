# Auction System

This is a Python-based distributed auction system that allows clients to place items up for auction and bid on items from other clients. The system uses advanced distributed systems techniques like dynamic host discovery, heartbeat-based fault tolerance, and leader election to ensure robust operation in a multi-host environment.

## Features

- **Distributed Architecture**: The system supports multiple servers and clients running on different machines.
- **Dynamic Host Discovery**: Automatically discovers new servers and clients, integrating them seamlessly into the network.
- **Fault Tolerance**: Implements heartbeat mechanisms to detect and handle failures.
- **Leader Election**: Ensures a designated leader for managing auctions and maintaining consistency across servers.
- **Client Functionality**: 
  - Place items for auction.
  - Bid on items provided by other clients.
- **Server Functionality**:
  - Manage the auction process.
  - Synchronize state between servers.

## Installation

### Prerequisites

- Python 3.8 or later

### Steps

1. Clone the repository:
   ```bash   
   git clone https://github.com/PiaWippermann/Dev_DSAuctSystem.git

## Usage

### Server
py server.py

### Client
py client.py

## Contact
 Pia Wippermann (814334)
 Aleksandar Sekulic (810154)
 Ali Haidar (810555) 
