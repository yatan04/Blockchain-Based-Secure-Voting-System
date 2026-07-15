import requests

BASE_URL = "http://localhost:5000"

def list_candidates():
    response = requests.get(f"{BASE_URL}/get_results")
    data = response.json()

    if 'results' in data:
        print("Registered Candidates:")
        for candidate in data['results']:
            print(f"ID: {candidate['candidate_id']}, Name: {candidate['name']}, Party: {candidate['party']}, Votes: {candidate['vote_count']}")
    else:
        print("No candidate data available or error:", data)

if __name__ == "__main__":
    list_candidates()
