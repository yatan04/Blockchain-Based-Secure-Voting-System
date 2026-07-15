import requests

BASE_URL = "http://localhost:5000"

def list_voters():
    response = requests.get(f"{BASE_URL}/get_chain")
    data = response.json()

    if 'chain' not in data:
        print("No blockchain data found or error:", data)
        return

    voters = {}
    # The voters are stored in memory in the blockchain object; since the chain API doesn't return voters,
    # Assuming you want to list from chain transactions:
    for block in data['chain']:
        for vote in block.get('transactions', []):
            voter_id_hash = vote['voter_id']
            if voter_id_hash not in voters:
                voters[voter_id_hash] = True

    print(f"Unique voters who have voted (hashed IDs): {len(voters)}")
    for voter_hash in voters:
        print(voter_hash)

if __name__ == "__main__":
    list_voters()
