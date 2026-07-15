import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time

# ----------------------------------------
# Backend API URL
# ----------------------------------------
BASE_URL = "http://127.0.0.1:5000"

CURRENT_USER_ID = None
CURRENT_ROLE = None  # "admin" or "voter" or None


# ----------------------------------------
# API Helper Functions
# ----------------------------------------
def api_post(endpoint, payload):
    try:
        r = requests.post(f"{BASE_URL}/{endpoint}", json=payload, timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"success": False, "message": f"❌ Backend not reachable: {e}"}


def api_get(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"success": False, "message": f"❌ Backend not reachable: {e}"}


# ----------------------------------------
# Entry Field Factory (Dark Theme)
# ----------------------------------------
def make_entry(parent, show=None):
    return tk.Entry(
        parent,
        width=40,
        bg="#222222",
        fg="#00ff88",
        insertbackground="#00ff88",
        relief="flat",
        highlightthickness=1,
        highlightbackground="#444444",
        highlightcolor="#00ff88",
        font=("Segoe UI", 11),
        show=show
    )


# ----------------------------------------
# Login + Role Update
# ----------------------------------------
def update_user_label():
    if CURRENT_USER_ID:
        user_label.config(text=f"👤 Logged in as: {CURRENT_USER_ID} ({CURRENT_ROLE})")
    else:
        user_label.config(text="👤 Not logged in")


def login_user():
    global CURRENT_USER_ID, CURRENT_ROLE

    user_id = entry_login_user.get().strip()
    password = entry_login_password.get().strip()

    if not user_id or not password:
        messagebox.showwarning("Missing Data", "Enter user ID and password/PIN.")
        return

    result = api_post("login", {
        "user_id": user_id,
        "password": password
    })

    if not result.get("success"):
        messagebox.showerror("Login Failed", result.get("message"))
        return

    CURRENT_USER_ID = result["user_id"]
    CURRENT_ROLE = result["role"]

    update_user_label()
    messagebox.showinfo("Login", f"Login successful → Role: {CURRENT_ROLE}")


def logout_user():
    global CURRENT_USER_ID, CURRENT_ROLE
    CURRENT_USER_ID = None
    CURRENT_ROLE = None
    update_user_label()
    messagebox.showinfo("Logout", "Logged out successfully.")


# ----------------------------------------
# UI Logic Functions
# ----------------------------------------
def register_voter():
    if CURRENT_ROLE != "admin":
        messagebox.showwarning("Unauthorized", "Only ADMIN can register voters.")
        return

    voter_id = entry_voter_id.get().strip()
    name = entry_voter_name.get().strip()
    email = entry_voter_email.get().strip()

    result = api_post("register_voter", {
        "role": CURRENT_ROLE,       # ADD THIS
        "voter_id": voter_id,
        "name": name,
        "email": email
    })

    pin = result.get("pin")
    msg = result.get("message", "No response")

    if pin:
        msg += f"\n\nGenerated PIN: {pin}"

    messagebox.showinfo("Response", msg)

def register_candidate():
    if CURRENT_ROLE != "admin":
        messagebox.showwarning("Unauthorized", "Only ADMIN can register candidates.")
        return

    cid = entry_candidate_id.get().strip()
    name = entry_candidate_name.get().strip()
    party = entry_candidate_party.get().strip()

    if not cid or not name or not party:
        messagebox.showwarning("Missing Data", "Please fill all candidate fields.")
        return

    result = api_post("register_candidate", {
        "candidate_id": cid,
        "name": name,
        "party": party
    })

    messagebox.showinfo("Response", result.get("message"))
    clear_candidate_inputs()
    update_status()
    load_candidate_dropdown()


def cast_vote():
    if CURRENT_ROLE != "voter":
        messagebox.showwarning("Unauthorized", "Only VOTERS can cast votes. Login as voter.")
        return

    candidate_id = select_vote_candidate.get().strip()
    voter_id = CURRENT_USER_ID

    if not candidate_id:
        messagebox.showwarning("Missing Data", "Select a candidate.")
        return

    result = api_post("cast_vote", {
        "voter_id": voter_id,
        "candidate_id": candidate_id
    })

    messagebox.showinfo("Response", result["message"])
    update_status()

def export_pdf():
    result = api_get("export_pdf")
    messagebox.showinfo("PDF Export", result.get("message", "Failed to export PDF"))

def mine_block():
    if CURRENT_ROLE != "admin":
        messagebox.showwarning("Unauthorized", "Only ADMIN can mine blocks.")
        return

    result = api_get("mine_block")
    messagebox.showinfo("Mining", result.get("message"))
    update_status()


def view_results():
    result = api_get("get_results")
    text_output.delete("1.0", tk.END)

    if "results" in result:
        text_output.insert(tk.END, "\n========== Election Results ==========\n\n")
        for c in result["results"]:
            text_output.insert(
                tk.END,
                f"{c['name']} ({c['party']}) → {c['vote_count']} votes\n"
            )
    else:
        text_output.insert(tk.END, result.get("message"))

    update_status()


def view_blockchain():
    if CURRENT_ROLE != "admin":
        messagebox.showwarning("Unauthorized", "Only ADMIN can view blockchain.")
        return

    result = api_get("get_chain")
    text_output.delete("1.0", tk.END)

    if "chain" in result:
        for block in result["chain"]:
            text_output.insert(tk.END, f"Block {block['index']}: {block['hash'][:25]}...\n")
    else:
        text_output.insert(tk.END, result.get("message"))

    update_status()


def validate_chain():
    if CURRENT_ROLE != "admin":
        messagebox.showwarning("Unauthorized", "Only ADMIN can validate blockchain.")
        return

    result = api_get("validate_chain")
    validation_output.delete("1.0", tk.END)

    if result.get("is_valid"):
        validation_output.insert(tk.END, "✔ BLOCKCHAIN IS VALID\n")
    else:
        validation_output.insert(tk.END, "❌ BLOCKCHAIN IS INVALID\n")

    validation_output.insert(tk.END, f"\nMessage: {result.get('message')}")


def update_status():
    try:
        requests.get(f"{BASE_URL}/get_results", timeout=2)
        status_label.config(text="🟢 Backend Online", foreground="#00ff88")
    except:
        status_label.config(text="🔴 Backend Offline", foreground="#ff4444")


def load_candidate_dropdown():
    result = api_get("get_results")
    if "results" in result:
        select_vote_candidate["values"] = [c["candidate_id"] for c in result["results"]]


# ----------------------------------------
# Clear Functions
# ----------------------------------------
def clear_voter_inputs():
    entry_voter_id.delete(0, tk.END)
    entry_voter_name.delete(0, tk.END)
    entry_voter_email.delete(0, tk.END)


def clear_candidate_inputs():
    entry_candidate_id.delete(0, tk.END)
    entry_candidate_name.delete(0, tk.END)
    entry_candidate_party.delete(0, tk.END)


# ----------------------------------------
# UI Setup
# ----------------------------------------
root = tk.Tk()
root.title("🗳 Blockchain Voting System")
root.geometry("950x720")
root.configure(bg="#1b1b1b")

style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background="#222222")
style.configure("TLabel", background="#222222", foreground="white", font=("Segoe UI", 11))
style.configure("TButton", font=("Segoe UI", 11, "bold"))
style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"))


# Top Status Bar
top_frame = ttk.Frame(root)
top_frame.pack(fill="x", pady=4)

status_label = ttk.Label(top_frame, text="Checking backend...", font=("Segoe UI", 10))
status_label.pack(side="left", padx=10)

user_label = ttk.Label(top_frame, text="👤 Not logged in", font=("Segoe UI", 10))
user_label.pack(side="right", padx=10)


# Notebook Tabs
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)


# ------------ LOGIN TAB ------------
tab_login = ttk.Frame(notebook)
notebook.add(tab_login, text="🔐 Login")

ttk.Label(tab_login, text="User ID (admin or voter id):").pack(pady=4)
entry_login_user = make_entry(tab_login)
entry_login_user.pack()

ttk.Label(tab_login, text="Password / PIN:").pack(pady=4)
entry_login_password = make_entry(tab_login, show="*")
entry_login_password.pack()

ttk.Button(tab_login, text="Login", command=login_user).pack(pady=8)
ttk.Button(tab_login, text="Logout", command=logout_user).pack(pady=8)

ttk.Label(tab_login, text="Admin Login → admin / admin123").pack(pady=12)


# ------------ REGISTER VOTER ------------
tab_voter = ttk.Frame(notebook)
notebook.add(tab_voter, text="🧍 Register Voter")

ttk.Label(tab_voter, text="Voter ID:").pack(pady=4)
entry_voter_id = make_entry(tab_voter)
entry_voter_id.pack()

ttk.Label(tab_voter, text="Name:").pack(pady=4)
entry_voter_name = make_entry(tab_voter)
entry_voter_name.pack()

ttk.Label(tab_voter, text="Email:").pack(pady=4)
entry_voter_email = make_entry(tab_voter)
entry_voter_email.pack()

ttk.Button(tab_voter, text="Register Voter", command=register_voter).pack(pady=10)


# ------------ REGISTER CANDIDATE (ADMIN) ------------
tab_candidate = ttk.Frame(notebook)
notebook.add(tab_candidate, text="🎭 Register Candidate")

ttk.Label(tab_candidate, text="Candidate ID:").pack(pady=4)
entry_candidate_id = make_entry(tab_candidate)
entry_candidate_id.pack()

ttk.Label(tab_candidate, text="Name:").pack(pady=4)
entry_candidate_name = make_entry(tab_candidate)
entry_candidate_name.pack()

ttk.Label(tab_candidate, text="Party:").pack(pady=4)
entry_candidate_party = make_entry(tab_candidate)
entry_candidate_party.pack()

ttk.Button(tab_candidate, text="Register Candidate", command=register_candidate).pack(pady=10)


# ------------ CAST VOTE (VOTER ONLY) ------------
tab_vote = ttk.Frame(notebook)
notebook.add(tab_vote, text="🗳 Cast Vote")

ttk.Label(tab_vote, text="Select Candidate:").pack(pady=4)
select_vote_candidate = ttk.Combobox(tab_vote, width=37)
select_vote_candidate.pack()

ttk.Button(tab_vote, text="Cast Vote", command=cast_vote).pack(pady=10)


# ------------ RESULTS + BLOCKCHAIN ------------
tab_results = ttk.Frame(notebook)
notebook.add(tab_results, text="📊 Results / Chain")

ttk.Button(tab_results, text="⛏ Mine Pending Votes (Admin)", command=mine_block).pack(pady=6)
ttk.Button(tab_results, text="📈 View Results", command=view_results).pack(pady=6)
ttk.Button(tab_results, text="🔗 View Blockchain (Admin)", command=view_blockchain).pack(pady=6)
ttk.Button(tab_results, text="📄 Export Results as PDF", command=export_pdf).pack(pady=6)

text_output = tk.Text(tab_results, height=20, width=100, bg="#111111", fg="#00ff88", insertbackground="#00ff88")
text_output.pack(pady=10)


# ------------ VALIDATE BLOCKCHAIN ------------
tab_validate = ttk.Frame(notebook)
notebook.add(tab_validate, text="🛡 Validate Blockchain")

ttk.Button(tab_validate, text="🛡 Validate (Admin)", command=validate_chain).pack(pady=10)

validation_output = tk.Text(tab_validate, height=10, width=80, bg="#111111", fg="#00ff88", insertbackground="#00ff88")
validation_output.pack(pady=10)


# Initial Loads
load_candidate_dropdown()
update_status()
update_user_label()


# Auto backend status refresh
def periodic_status_check():
    while True:
        update_status()
        time.sleep(4)

threading.Thread(target=periodic_status_check, daemon=True).start()


root.mainloop()
