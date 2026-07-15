"""
Blockchain-Based Secure Voting System
======================================
This system implements a decentralized, secure, and transparent voting platform using:
1. Blockchain technology for immutable vote storage
2. Cryptographic hashing (SHA-256) for security
3. Voter authentication and registration
4. Smart contract-like voting logic
5. Flask web interface for user interaction

Dependencies:
- Flask: pip install Flask
- hashlib (built-in)
- datetime (built-in)
- json (built-in)
"""

import hashlib
import json
import time
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from uuid import uuid4
import sqlite3
import random

from database import setup_database, get_db

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def seed_admin():
    """Create default admin user if not exists."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", ('admin',))
    exists = c.fetchone()[0]
    if exists == 0:
        c.execute(
            "INSERT INTO users (user_id, password, role) VALUES (?, ?, ?)",
            ('admin', 'admin123', 'admin')
        )
        conn.commit()
        print("Default admin created: username=admin, password=admin123")
    conn.close()



class Voter:
    """Represents a registered voter"""

    def __init__(self, voter_id, name, email):
        self.voter_id = voter_id
        self.name = name
        self.email = email
        self.has_voted = False
        self.registration_time = datetime.now().isoformat()

    def to_dict(self):
        """Convert voter to dictionary"""
        return {
            'voter_id': self.voter_id,
            'name': self.name,
            'email': self.email,
            'has_voted': self.has_voted,
            'registration_time': self.registration_time
        }


class Candidate:
    """Represents a candidate in the election"""

    def __init__(self, candidate_id, name, party):
        self.candidate_id = candidate_id
        self.name = name
        self.party = party
        self.vote_count = 0

    def to_dict(self):
        """Convert candidate to dictionary"""
        return {
            'candidate_id': self.candidate_id,
            'name': self.name,
            'party': self.party,
            'vote_count': self.vote_count
        }


class Block:
    """Represents a block in the blockchain"""

    def __init__(self, index, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions  # List of votes
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """Calculate SHA-256 hash of the block"""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)

        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        """Mine the block with proof of work"""
        target = '0' * difficulty

        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

        print(f"Block mined: {self.hash}")
        return self.hash

    def to_dict(self):
        """Convert block to dictionary"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }


class VotingBlockchain:
    """Blockchain with SQLite persistence"""

    def __init__(self):
        setup_database()  # Ensure DB exists

        self.chain = []
        self.pending_votes = []
        self.voters = {}
        self.candidates = {}
        self.difficulty = 2

        # Load DB data
        self.load_voters_from_db()
        self.load_candidates_from_db()
        self.load_chain_from_db()

        # If no chain found, create genesis block and save it
        if len(self.chain) == 0:
            genesis = self.create_and_store_genesis_block()
            self.save_block_to_db(genesis)

    # ---------------- DATABASE LOADING ----------------

    def load_voters_from_db(self):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT voter_id, name, email, has_voted FROM voters")
        rows = c.fetchall()
        conn.close()

        for voter_id, name, email, has_voted in rows:
            v = Voter(voter_id, name, email)
            v.has_voted = bool(has_voted)
            self.voters[voter_id] = v

    def load_candidates_from_db(self):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT candidate_id, name, party, vote_count FROM candidates")
        rows = c.fetchall()
        conn.close()

        for candidate_id, name, party, vote_count in rows:
            cand = Candidate(candidate_id, name, party)
            cand.vote_count = vote_count
            self.candidates[candidate_id] = cand

    def save_block_to_db(self, block):
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO blocks (index_no, timestamp, transactions, previous_hash, nonce, hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
        block.index,
        block.timestamp,
        json.dumps(block.transactions),
        block.previous_hash,
        block.nonce,
        block.hash
    ))
        conn.commit()
        conn.close()


    def load_chain_from_db(self):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT index_no, timestamp, transactions, previous_hash, nonce, hash FROM blocks ORDER BY index_no")
        rows = c.fetchall()
        conn.close()

        self.chain = []

        for idx, ts, tx, prev_hash, nonce, h in rows:
            block = Block(idx, json.loads(tx), prev_hash)
            block.timestamp = ts
            block.nonce = nonce
            block.hash = h
            self.chain.append(block)


    # ---------------- WRITE TO DATABASE ----------------

    def save_voter_to_db(self, voter: Voter):
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO voters (voter_id, name, email, has_voted) VALUES (?, ?, ?, ?)",
            (voter.voter_id, voter.name, voter.email, int(voter.has_voted))
        )
        conn.commit()
        conn.close()

    def save_candidate_to_db(self, candidate: Candidate):
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO candidates (candidate_id, name, party, vote_count) VALUES (?, ?, ?, ?)",
            (candidate.candidate_id, candidate.name, candidate.party, candidate.vote_count)
        )
        conn.commit()
        conn.close()

    def save_block_to_db(self, block):
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO blocks (index_no, timestamp, transactions, previous_hash, nonce, hash) VALUES (?, ?, ?, ?, ?, ?)",
            (
                block.index,
                block.timestamp,
                json.dumps(block.transactions),
                block.previous_hash,
                block.nonce,
                block.hash
            )
        )
        conn.commit()
        conn.close()

    # ---------------- CORE FEATURES ----------------

    def create_and_store_genesis_block(self):
        genesis = Block(0, [], "0")
        genesis.hash = genesis.calculate_hash()
        self.chain.append(genesis)
        self.save_block_to_db(genesis)

    def register_voter(self, voter_id, name, email):
        if voter_id in self.voters:
            return {'success': False, 'message': 'Voter already registered'}

        v = Voter(voter_id, name, email)
        self.voters[voter_id] = v
        self.save_voter_to_db(v)

        return {'success': True, 'message': 'Voter registered successfully'}

    def register_candidate(self, candidate_id, name, party):
        if candidate_id in self.candidates:
            return {'success': False, 'message': 'Candidate already exists'}

        c = Candidate(candidate_id, name, party)
        self.candidates[candidate_id] = c
        self.save_candidate_to_db(c)

        return {'success': True, 'message': 'Candidate registered successfully'}

    def cast_vote(self, voter_id, candidate_id):
        if voter_id not in self.voters:
            return {'success': False, 'message': 'Voter not found'}

        if self.voters[voter_id].has_voted:
            return {'success': False, 'message': 'Voter already voted'}

        if candidate_id not in self.candidates:
            return {'success': False, 'message': 'Candidate not found'}

        vote = {
            'voter_id': voter_id,
            'candidate_id': candidate_id,
            'timestamp': time.time()
        }
        self.pending_votes.append(vote)

        # Update voter + candidate
        self.voters[voter_id].has_voted = True
        self.candidates[candidate_id].vote_count += 1

        self.save_voter_to_db(self.voters[voter_id])
        self.save_candidate_to_db(self.candidates[candidate_id])

        return {'success': True, 'message': 'Vote cast successfully'}

    def mine_pending_votes(self):
        if len(self.pending_votes) == 0:
            return {'success': False, 'message': 'No votes to mine'}

        last = self.chain[-1]
        new_block = Block(len(self.chain), self.pending_votes, last.hash)
        new_block.mine_block(self.difficulty)

        self.chain.append(new_block)

        # SAVE block permanently
        self.save_block_to_db(new_block)

        self.pending_votes = []

        return {
            'success': True,
            'message': 'Block mined and stored in DB',
            'block': new_block.to_dict()
        }


    def get_election_results(self):
        return sorted([c.to_dict() for c in self.candidates.values()],
                      key=lambda x: x['vote_count'],
                      reverse=True)

    def validate_chain(self):
        return all(
            self.chain[i].hash == self.chain[i].calculate_hash() and
            self.chain[i].previous_hash == self.chain[i - 1].hash
            for i in range(1, len(self.chain))
        )


# Flask Web Application
app = Flask(__name__)

# Setup DB and seed admin
setup_database()
seed_admin()

# Blockchain in memory (votes/candidates still kept here)
blockchain = VotingBlockchain()


# Generate a unique node identifier
node_identifier = str(uuid4()).replace('-', '')

@app.route('/export_pdf', methods=['GET'])
def export_pdf():
    filename = "election_results.pdf"

    results = blockchain.get_election_results()

    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, "Election Results Report")
    c.setFont("Helvetica", 12)

    y = 700

    for r in results:
        line = f"{r['name']} ({r['party']}): {r['vote_count']} votes"
        c.drawString(100, y, line)
        y -= 25

    c.save()

    return jsonify({
        "success": True,
        "message": f"PDF generated: {filename}"
    })

@app.route('/')
def index():
    """Home page with voting interface"""
    html = """
    <!DOCTYPE html>
    <html><head><title>Blockchain Voting System</title></head>
    <body style="font-family: Arial; margin: 40px; background: #f0f0f0;">
        <div style="background: white; padding: 30px; border-radius: 10px;">
            <h1>🗳️ Blockchain Voting System</h1>
            <p>Endpoints: /register_voter, /register_candidate, /cast_vote, /mine_block, /get_chain, /get_results</p>
        </div>
    </body></html>
    """
    return render_template_string(html)

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint for admin and voters"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    password = data.get('password')

    if not user_id or not password:
        return jsonify({'success': False, 'message': 'Missing user_id or password'}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT password, role FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    if row is None:
        return jsonify({'success': False, 'message': 'User not found'}), 401

    stored_password, role = row
    if stored_password != password:
        return jsonify({'success': False, 'message': 'Invalid password/PIN'}), 401

    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user_id': user_id,
        'role': role
    }), 200


@app.route('/register_voter', methods=['POST'])
def register_voter():
    """API endpoint to register a voter (ADMIN ONLY) and create PIN login"""
    values = request.get_json()

    # Check if admin is performing the action
    role = values.get("role")
    if role != "admin":  
        return jsonify({
            'success': False,
            'message': '❌ Only ADMIN can register voters.'
        }), 403

    required = ['voter_id', 'name', 'email']
    if not all(k in values for k in required):
        return jsonify({'success': False, 'message': 'Missing values'}), 400

    # Register in blockchain (same as before)
    result = blockchain.register_voter(
        values['voter_id'],
        values['name'],
        values['email']
    )

    # If successful → create PIN login
    if result.get('success'):
        voter_id = values['voter_id']

        # Generate 4-digit PIN
        pin = str(random.randint(1000, 9999))

        conn = get_db()
        c = conn.cursor()

        # Insert or replace voter user (role=voter)
        c.execute(
            "INSERT OR REPLACE INTO users (user_id, password, role) VALUES (?, ?, ?)",
            (voter_id, pin, 'voter')
        )

        conn.commit()
        conn.close()

        result['pin'] = pin  # send PIN back to UI

    return jsonify(result), 200



@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    """API endpoint to register a candidate"""
    values = request.get_json()

    required = ['candidate_id', 'name', 'party']
    if not all(k in values for k in required):
        return jsonify({'success': False, 'message': 'Missing values'}), 400

    result = blockchain.register_candidate(
        values['candidate_id'],
        values['name'],
        values['party']
    )

    return jsonify(result), 200


@app.route('/cast_vote', methods=['POST'])
def cast_vote():
    """API endpoint to cast a vote"""
    values = request.get_json()

    required = ['voter_id', 'candidate_id']
    if not all(k in values for k in required):
        return jsonify({'success': False, 'message': 'Missing values'}), 400

    result = blockchain.cast_vote(
        values['voter_id'],
        values['candidate_id']
    )

    return jsonify(result), 200


@app.route('/mine_block', methods=['GET'])
def mine_block():
    """API endpoint to mine pending votes"""
    result = blockchain.mine_pending_votes()
    return jsonify(result), 200


@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': [b.to_dict() for b in blockchain.chain],
        'length': len(blockchain.chain),
        'is_valid': blockchain.validate_chain()
    }
    return jsonify(response), 200


@app.route('/get_results', methods=['GET'])
def get_results():
    """API endpoint to get election results"""
    results = blockchain.get_election_results()
    return jsonify({
        'results': results,
        'total_votes': sum(c['vote_count'] for c in results)
    }), 200


@app.route('/validate_chain', methods=['GET'])
def validate_chain():
    """API endpoint to validate blockchain"""
    is_valid = blockchain.validate_chain()
    return jsonify({
        'is_valid': is_valid,
        'message': 'Blockchain is valid' if is_valid else 'Blockchain is invalid'
    }), 200


if __name__ == '__main__':
    # Sample data for testing
    print("Initializing Blockchain Voting System...")
    print("=" * 60)

    # Register sample candidates
    blockchain.register_candidate('C001', 'Alice Johnson', 'Democratic Party')
    blockchain.register_candidate('C002', 'Bob Smith', 'Republican Party')
    blockchain.register_candidate('C003', 'Charlie Davis', 'Independent')

    print("Sample candidates registered")
    print("=" * 60)
    print("\nStarting Flask server...")
    print("Open http://localhost:5000 in your browser")
    print("\nAPI Endpoints:")
    print("  POST /register_voter - Register a new voter")
    print("  POST /register_candidate - Register a new candidate")
    print("  POST /cast_vote - Cast a vote")
    print("  GET  /mine_block - Mine pending votes")
    print("  GET  /get_chain - View blockchain")
    print("  GET  /get_results - View election results")
    print("  GET  /validate_chain - Validate blockchain")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
