# Blockchain-Based Secure Voting System

A decentralized, transparent, and tamper-proof voting platform built with blockchain technology, cryptographic hashing, and a Flask web API with Tkinter desktop interface.

## Features

- **Blockchain Integrity**: Immutable vote storage using SHA-256 hashing and proof-of-work consensus
- **Voter Authentication**: Secure registration, login, and role-based access (Admin / Voter)
- **Election Management**: Create elections, add candidates, set voting windows
- **Real-time Voting**: Cast votes via web API or desktop GUI with instant blockchain recording
- **Transparent Tallying**: Publicly verifiable vote counts with cryptographic audit trail
- **Admin Dashboard**: Election monitoring, voter management, result publication
- **PDF Receipts**: Generate cryptographic vote receipts for voters

## Architecture

```
┌─────────────────┐     HTTP/JSON       ┌──────────────────┐
│  Tkinter GUI    │ ◄─────────────────► │   Flask API      │
│  (voting_ui.py) │                     │  (blockchain_    │
└─────────────────┘                     │   voting_system) │
                                        └────────┬─────────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │     SQLite Database     │
                                    │  (users, elections,     │
                                    │   votes, blockchain)    │
                                    └─────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Blockchain Core | Python (hashlib, json, time) |
| Backend API | Flask |
| Database | SQLite |
| Desktop UI | Tkinter |
| Cryptography | SHA-256, Proof-of-Work |
| PDF Generation | ReportLab |

## Project Structure

```
Blockchain-Based-Secure-Voting-System/
├── blockchain_voting_system.py   # Core blockchain + Flask API
├── voting_ui.py                  # Tkinter desktop client
├── database.py                   # SQLite schema & helpers
├── candidate_list.py             # Candidate management
├── voter_list.py                 # Voter management
├── commands.txt                  # CLI reference
├── voting.db                     # SQLite database (auto-created)
└── README.md
```

## Quick Start

### Prerequisites
```bash
pip install flask reportlab requests
```

### 1. Start the Flask Backend
```bash
python blockchain_voting_system.py
# Server runs at http://127.0.0.1:5000
```

### 2. Launch the Desktop GUI
```bash
python voting_ui.py
```

### 3. Default Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Voter | (register via admin) | PIN-based |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | User login (returns role) |
| POST | `/register` | Register new voter (admin only) |

### Elections
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/create_election` | Create new election (admin) |
| GET | `/elections` | List all elections |
| GET | `/election/<id>` | Get election details |
| POST | `/start_election/<id>` | Start election (admin) |
| POST | `/end_election/<id>` | End election (admin) |

### Voting
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/vote` | Cast vote (voter) |
| GET | `/results/<election_id>` | Get tally (public after election ends) |

### Blockchain
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/chain` | Full blockchain |
| GET | `/block/<index>` | Single block |
| GET | `/validate` | Verify chain integrity |

## Blockchain Design

### Block Structure
```json
{
  "index": 3,
  "timestamp": 1699876543.12,
  "transactions": [
    {"voter_id": "V001", "candidate_id": "C02", "election_id": "E01"}
  ],
  "previous_hash": "0000a3f2...",
  "nonce": 18472,
  "hash": "0000f8b1..."
}
```

### Consensus
- **Proof-of-Work**: Difficulty 4 (leading `0000` in hash)
- **Immutability**: Changing any block invalidates all subsequent hashes
- **Validation**: `/validate` endpoint verifies entire chain integrity

## Security Features

1. **Vote Privacy**: Voter identity separated from vote in blockchain (pseudonymous voter_id)
2. **Double-Vote Prevention**: Database constraint + blockchain check
3. **Tamper Evidence**: Any block modification breaks chain validation
4. **Access Control**: Role-based endpoints (admin vs voter)
5. **Audit Trail**: Complete transaction history with timestamps

## Database Schema

```sql
-- Users (voters + admins)
CREATE TABLE users (
  user_id TEXT PRIMARY KEY,
  password_hash TEXT NOT NULL,
  role TEXT CHECK(role IN ('admin','voter')) NOT NULL
);

-- Elections
CREATE TABLE elections (
  election_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  status TEXT CHECK(status IN ('upcoming','active','ended'))
);

-- Candidates
CREATE TABLE candidates (
  candidate_id TEXT PRIMARY KEY,
  election_id TEXT REFERENCES elections(election_id),
  name TEXT NOT NULL,
  party TEXT,
  vote_count INTEGER DEFAULT 0
);

-- Votes (blockchain transactions)
CREATE TABLE votes (
  vote_id TEXT PRIMARY KEY,
  voter_id TEXT REFERENCES users(user_id),
  candidate_id TEXT REFERENCES candidates(candidate_id),
  election_id TEXT REFERENCES elections(election_id),
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  block_hash TEXT
);
```

## Usage Flow

### Admin
1. Login as `admin` / `admin123`
2. Create election → Add candidates → Set dates
3. Register voters (auto-generates PIN)
4. Start election → Monitor via `/chain` or GUI
5. End election → Publish results

### Voter
1. Receive voter_id + PIN from admin
2. Login via GUI or API
3. Select active election → Choose candidate
4. Submit vote → Receive PDF receipt
5. Verify vote on blockchain via `/block/<index>`

## Commands Reference (`commands.txt`)

```bash
# Start backend
python blockchain_voting_system.py

# Start GUI
python voting_ui.py

# View chain (API)
curl http://127.0.0.1:5000/chain

# Validate chain
curl http://127.0.0.1:5000/validate
```

## Future Improvements

- [ ] Web-based voter portal (React/Vue frontend)
- [ ] Zero-knowledge proofs for vote privacy
- [ ] Multi-node P2P blockchain network
- [ ] Smart contract integration (Ethereum/Polygon)
- [ ] Biometric voter authentication
- [ ] Mobile app (Flutter/React Native)
- [ ] Automated testing suite

## License

MIT License — Free for educational and research use.

## Author

**Yatan Sehrawat** — [@yatan04](https://github.com/yatan04)
