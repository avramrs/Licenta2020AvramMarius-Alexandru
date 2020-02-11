import tkinter as tk
from client import Client
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import sys


class Booth(tk.Frame):
    def __init__(self, master, counter_addr):
        super().__init__(master)
        self.master = master
        self.client = Client(counter_addr)
        master.title('Voting Booth')
        # Width height
        master.geometry("600x400")
        # Create widgets/grid
        self.pack()
        self.create_widgets()
        # Init selected item var

    def create_widgets(self):
        self.message_box = tk.LabelFrame(self.master, text="Messages")
        self.btn_frame = tk.Frame(self.master, pady=20)

        self.ID_text = tk.StringVar()
        self.message = tk.StringVar()
        self.list_btn_text = tk.StringVar()
        self.list_btn_text.set("Voter list")
        self.set_message()

        self.ID_label = tk.Label(self.btn_frame, text="ID")
        self.ID_entry = tk.Entry(self.btn_frame, textvariable=self.ID_text, width=60)
        self.message_label = tk.Message(self.message_box, textvariable=self.message, width=580)

        self.send_btn = tk.Button(self.btn_frame, text="Send Vote", width=12, command=self.send_vote)
        self.key_btn = tk.Button(self.btn_frame, text="Load Key", width=12, command=self.load_key)
        self.results_btn = tk.Button(self.btn_frame, text="Get Results", width=12, command=self.get_results)
        self.voters_btn = tk.Button(self.btn_frame, text=self.list_btn_text.get(), width=12, command=self.get_voters)
        self.open_btn = tk.Button(self.btn_frame, text="Open Vote", width=12, command=self.open_vote)

        self.message_box.pack(side="top", fill="both", expand="yes")
        self.btn_frame.pack(side="bottom", pady=10)
        self.message_label.grid(row=0)
        self.ID_label.grid(row=0, column=1)
        self.ID_entry.grid(row=0, column=2, columnspan=3)
        self.send_btn.grid(row=1, column=1)
        self.open_btn.grid(row=1, column=2)
        self.key_btn.grid(row=1, column=3)
        self.results_btn.grid(row=1, column=4)
        self.voters_btn.grid(row=1, column=5)

    def set_message(self):
        if self.client.key is None:
            self.message.set("Please Load a key")
        else:
            question = self.client.get_question()
            self.message.set(question["question"])
            self.question = question["question"]
            self.answers = question["answers"]
            self.radio_btns = []
            self.radio_value = tk.IntVar(value=0)
            if self.answers is None:
                return
            for i, answer in enumerate(question["answers"]):
                btn = tk.Radiobutton(self.message_box, text=answer, variable=self.radio_value, value=i + 1, anchor="w",
                                     command=self.get_answer)
                self.radio_btns.append(btn)
                btn.grid(row=i + 1, sticky="w")

    def get_answer(self):
        print(self.radio_value.get())

    def forget_radio(self):
        self.radio_value.set(0)
        if self.radio_btns:
            for btn in self.radio_btns:
                btn.grid_forget()

    def send_vote(self):
        ID = self.ID_entry.get()
        if not ID:
            messagebox.showinfo("Missing ID", "Please enter ID and try again.")
        else:
            self.client.set_ID(ID)
            answer_idx = self.radio_value.get() - 1
            self.client.message = self.answers[answer_idx]
            print(self.answers[answer_idx])
            self.forget_radio()
            # try:
            #     self.client.get_admin_sig()
            # except AttributeError:
            #     self.message.set("Wrong ID or Voting ended.")
            # except Exception as e:
            #     print(e)
            #     self.message.set("Vote server is down.")

    def open_vote(self):
        if self.client.admin_sig is None:
            filename = askopenfilename(initialdir="", title="Select file")
            if filename:
                self.client.load_sig(filename)
            else:
                return
        try:
            self.client.open_vote()
        except:
            messagebox.showinfo("Message Missing", "Vote not found in voter list.")

    def load_key(self):
        filename = askopenfilename(initialdir="", title="Select file",
                                   filetypes=(("pem files", "*.pem"), ("all files", "*.*")))
        print(filename)
        if filename:
            self.client.load_key(filename)
        self.set_message()

    def get_results(self):
        results = self.client.get_results()
        self.forget_radio()
        if results is None:
            self.message.set("Still counting votes.")
        else:
            msg = self.question+"\n"
            for i, r in enumerate(results):
                msg += "{a}:{r}\n".format(a=self.answers[i], r=r)
            self.message.set(msg)

    def get_voters(self):
        if not self.client.admin_sig:
            self.missing_id_msg = messagebox.showinfo("Signature missing",
                                                      "No signature found.\nYou must first send a vote.")
            return
        self.forget_radio()
        voters = self.client.get_voters()
        if voters:
            msg = ""
            for voter in voters:
                msg += "l:{l},x:{x},y:{y}\n".format(y=str(voter["y"]), x=str(voter["x"]), l=str(voter["l"]))
            self.message.set(msg)
        else:
            self.message.set("Vote in progress.")


if len(sys.argv) != 2:
    raise AttributeError("Counter address parameter missing.")
else:
    print("Counter:{s}".format(s=sys.argv[1]))

root = tk.Tk()
app = Booth(counter_addr=sys.argv[1], master=root)
app.mainloop()
